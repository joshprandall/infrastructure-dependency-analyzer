#!/usr/bin/env python3
"""Analyze declared service dependencies locally. No discovery or network access."""
import argparse
from collections import deque
import html
import json
import math
from pathlib import Path
import re
import sys

MAX_SERVICES = 200


def load_inventory(path):
    path = Path(path)
    if path.stat().st_size > 2_000_000:
        raise ValueError('Inventory must be no larger than 2 MB.')
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return validate(json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_keys))


def validate(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1 or isinstance(data.get('schema_version'), bool):
        raise ValueError('Expected an object with schema_version: 1.')
    if not isinstance(data.get('services'), list) or not 1 <= len(data['services']) <= MAX_SERVICES:
        raise ValueError(f'Provide between 1 and {MAX_SERVICES} services.')
    services = {}
    for row in data['services']:
        if not isinstance(row, dict):
            raise ValueError('Each service must be an object.')
        key = row.get('id')
        if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', key):
            raise ValueError('Service IDs must be lowercase slugs, starting with a letter, at most 64 characters.')
        if key in services:
            raise ValueError('Duplicate service ID: ' + key)
        for field in ['name', 'owner', 'site', 'purpose']:
            if not isinstance(row.get(field), str) or len(row[field]) > 500:
                raise ValueError(f'{key}: {field} must be a string of at most 500 characters.')
        if not row['name'].strip():
            raise ValueError(key + ': name must not be empty.')
        if row.get('kind') not in ['infrastructure', 'application', 'business']:
            raise ValueError(key + ': kind must be infrastructure, application, or business.')
        rto = row.get('rto_hours')
        if isinstance(rto, bool) or not isinstance(rto, (int, float)) or not math.isfinite(rto) or rto <= 0:
            raise ValueError(key + ': rto_hours must be positive and finite.')
        deps = row.get('depends_on')
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            raise ValueError(key + ': depends_on must be a list of service IDs.')
        if len(deps) != len(set(deps)):
            raise ValueError(key + ': duplicate dependencies.')
        services[key] = {**row, 'depends_on': sorted(deps)}
    for key, row in services.items():
        for dependency in row['depends_on']:
            if dependency not in services:
                raise ValueError(f'{key}: unknown dependency {dependency}.')
    title = data.get('title', 'Service dependency inventory')
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('title must be a nonempty string of at most 200 characters.')
    return {'schema_version': 1, 'title': title, 'services': [services[k] for k in sorted(services)]}


class Model:
    def __init__(self, inventory):
        self.inventory = validate(inventory)
        self.services = {r['id']: r for r in self.inventory['services']}
        self.reverse = {key: [] for key in self.services}
        for key, row in self.services.items():
            for dep in row['depends_on']:
                self.reverse[dep].append(key)
        for dependents in self.reverse.values():
            dependents.sort()

    def impact(self, root):
        """BFS of reverse edges returns one shortest explanatory path per service."""
        if root not in self.services:
            raise ValueError('Unknown scenario service: ' + root)
        paths = {root: [root]}
        queue = deque([root])
        while queue:
            current = queue.popleft()
            for dependent in self.reverse[current]:
                if dependent not in paths:
                    paths[dependent] = paths[current] + [dependent]
                    queue.append(dependent)
        affected = sorted((key for key in paths if key != root), key=lambda k: (len(paths[k]), k))
        return {
            'root': root,
            'direct': self.reverse[root],
            'affected': affected,
            'business_services': sorted(k for k in paths if self.services[k]['kind'] == 'business'),
            'paths': {k: paths[k] for k in affected},
            'owners': sorted({self.services[k]['owner'].strip() for k in paths if self.services[k]['owner'].strip()}),
            'sites': sorted({self.services[k]['site'].strip() for k in paths if self.services[k]['site'].strip()}),
            'prerequisite_plan': self.prerequisite_plan(set(paths)),
        }

    def prerequisite_plan(self, targets):
        """Topological waves of targets plus their prerequisite closure.

        Includes healthy prerequisites: these are validation checkpoints, not
        inferred failures. Cycles and all nodes blocked by cycles stay unresolved.
        """
        selected = set(targets)
        stack = list(selected)
        while stack:
            current = stack.pop()
            for dependency in self.services[current]['depends_on']:
                if dependency not in selected:
                    selected.add(dependency)
                    stack.append(dependency)
        pending = set(selected)
        waves = []
        done = set()
        while pending:
            ready = sorted(k for k in pending if set(self.services[k]['depends_on']) <= done)
            if not ready:
                break
            waves.append(ready)
            done.update(ready)
            pending.difference_update(ready)
        return {'waves': waves, 'unresolved': sorted(pending)}

    def cycles(self):
        """Tarjan SCCs identify cycle groups without enumerating every cycle."""
        index = {}
        low = {}
        stack = []
        active = set()
        groups = []
        def visit(key):
            index[key] = low[key] = len(index)
            stack.append(key)
            active.add(key)
            for dep in self.services[key]['depends_on']:
                if dep not in index:
                    visit(dep)
                    low[key] = min(low[key], low[dep])
                elif dep in active:
                    low[key] = min(low[key], index[dep])
            if low[key] == index[key]:
                group = []
                while True:
                    node = stack.pop()
                    active.remove(node)
                    group.append(node)
                    if node == key:
                        break
                if len(group) > 1 or key in self.services[key]['depends_on']:
                    groups.append(sorted(group))
        for key in self.services:
            if key not in index:
                visit(key)
        return sorted(groups)

    def report(self):
        scenarios = {k: self.impact(k) for k in self.services}
        gaps = []
        for key, row in self.services.items():
            for field in ['owner', 'site', 'purpose']:
                if not row[field].strip():
                    gaps.append({'code': 'MISSING_' + field.upper(), 'service': key, 'detail': f'{field} is not recorded.'})
            for dependency in row['depends_on']:
                dep = self.services[dependency]
                if dep['rto_hours'] > row['rto_hours']:
                    gaps.append({'code': 'RTO_ALIGNMENT_REVIEW', 'service': key, 'detail': f"Dependency {dependency} has a {dep['rto_hours']:g}h recovery target versus {row['rto_hours']:g}h for this service."})
        cycle_groups = self.cycles()
        for group in cycle_groups:
            gaps.append({'code': 'DEPENDENCY_CYCLE', 'service': ', '.join(group), 'detail': 'Circular prerequisites need explicit recovery planning.'})
        ranked = sorted(self.services, key=lambda k: (-len(scenarios[k]['business_services']), -len(scenarios[k]['affected']), k))
        return {'inventory': self.inventory, 'scenarios': scenarios, 'cycle_groups': cycle_groups, 'findings': gaps, 'ranking': ranked,
                'limits': 'Potential impact under declared hard dependencies. Not live monitoring, outage prediction, or proof of recovery. No redundancy, partial degradation, or conditional dependency modeling.'}


def markdown(report, root=None):
    def text(value):
        return html.escape(str(value)).replace('|', '&#124;').replace('\n', ' ').replace('\r', ' ')
    services = {s['id']: s for s in report['inventory']['services']}
    lines = ['# ' + text(report['inventory']['title']), '', report['limits'], '', '## Review findings', '']
    if not report['findings']:
        lines.append('No recorded gaps under the implemented checks.')
    for f in report['findings']:
        lines.append(f"- **{text(f['code'])} / {text(f['service'])}:** {text(f['detail'])}")
    lines += ['', '## Dependency concentration', '', 'Ranked by potentially affected business services, then downstream services. This is not a risk score or proof of a single point of failure.', '', '| Service | Downstream services | Business services including selected root |', '| --- | ---: | ---: |']
    for key in report['ranking']:
        s = report['scenarios'][key]
        lines.append(f"| {text(services[key]['name'])} | {len(s['affected'])} | {len(s['business_services'])} |")
    if root is not None:
        scenario = report['scenarios'][root]
        lines += ['', '## Scenario: ' + text(services[root]['name']), '', 'Selected service is excluded from the downstream count. Paths run from unavailable prerequisite to dependent consumer.', '']
        for key in scenario['affected']:
            path = ' → '.join(services[n]['name'] for n in scenario['paths'][key])
            lines.append('- ' + text(path))
        if not scenario['affected']:
            lines.append('No downstream services are recorded; the selected service itself may still be business-critical.')
        lines += ['', '### Prerequisite validation waves', '', 'These include healthy prerequisites. They are not outage diagnoses, restore instructions, or duration estimates.', '']
        for n, wave in enumerate(scenario['prerequisite_plan']['waves'], 1):
            lines.append(f"{n}. " + ', '.join(text(services[k]['name']) for k in wave))
        if scenario['prerequisite_plan']['unresolved']:
            lines.append('Unresolved due to cycles or dependence on cycles: ' + ', '.join(scenario['prerequisite_plan']['unresolved']))
    return '\n'.join(lines) + '\n'


def html_report(report):
    template = Path(__file__).with_name('report-template.html').read_text(encoding='utf-8')
    # Embedded application/json must not be able to terminate its script element.
    payload = json.dumps(report, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return template.replace('__REPORT_JSON__', payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--service', help='Service ID for a focused Markdown scenario')
    parser.add_argument('--format', choices=['markdown', 'json', 'html'], default='markdown')
    parser.add_argument('--output', type=Path, help='New report path; existing files require --overwrite')
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--fail-on-findings', action='store_true', help='Exit 1 when model review findings exist')
    args = parser.parse_args(argv)
    try:
        model = Model(load_inventory(args.inventory))
        if args.service and args.service not in model.services:
            raise ValueError('Unknown service: ' + args.service)
        if args.service and args.format != 'markdown':
            raise ValueError('--service applies only to Markdown; JSON and HTML include all scenarios.')
        if args.output and args.output.resolve() == args.inventory.resolve():
            raise ValueError('The output must not overwrite the input inventory.')
        report = model.report()
        content = json.dumps(report, indent=2) + '\n' if args.format == 'json' else html_report(report) if args.format == 'html' else markdown(report, args.service)
        if args.output:
            with args.output.open('w' if args.overwrite else 'x', encoding='utf-8') as stream:
                stream.write(content)
            print('Saved ' + str(args.output))
        else:
            print(content, end='')
        return 1 if args.fail_on_findings and report['findings'] else 0
    except (OSError, ValueError, RecursionError) as exc:
        print('Input/output error: ' + str(exc), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
