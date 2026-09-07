# Infrastructure Dependency Analyzer

Trace the potential business impact of an unavailable service using a declared infrastructure inventory. Generate an interactive offline report, explain dependency paths, detect circular prerequisites, and identify recovery-target alignment questions.

The included scenario models a **fictional construction business** with office and field services. It does not describe any real employer’s architecture.

## Start with the demo

Download and extract the repository, then open **`examples/interactive-report.html`** in a browser. No installation or account is required for the included report.

- Select an unavailable service.
- Inspect potentially affected workflows, recorded owners, and locations.
- Expand the dependency paths explaining each result.
- Review prerequisite validation waves and model findings.
- Filter the affected-service table or print the current scenario.

The report is a snapshot. To reflect an edited inventory, regenerate it with Python.

## Run the analyzer

Python **3.10+**, standard library only. Run these commands from the project folder. On Windows, use `py` if `python` is unavailable.

```sh
# Print a focused scenario report
python analyzer.py examples/construction-services.json --service office-internet

# Generate a NEW interactive report
python analyzer.py examples/construction-services.json --format html --output my-report.html

# Machine-readable analysis of all scenarios
python analyzer.py examples/construction-services.json --format json --output my-analysis.json

# Run the tests
python -m unittest discover -s tests -v

# Inspect a deliberately circular prerequisite example
python analyzer.py examples/circular-services.json --service auth
```

Existing output files require `--overwrite`. The input inventory cannot be overwritten. Output folders must already exist.

Exit codes: **0** = report generated; **1** = model review findings when `--fail-on-findings` is supplied; **2** = input/output error. Findings do not stop report generation. `--service` applies only to Markdown; JSON and HTML always contain every scenario.

## Example outcome

With **Office internet** selected, the fictional model identifies six downstream services, including three business workflows: field dispatch, field time entry, and office project coordination. Office payroll is not included in that particular scenario because its declared prerequisites are internal.

That exclusion is a modeling result, not a claim that real payroll never needs internet access. Missing or inaccurate dependencies change the answer.

The sample also contains two review findings:

- The ERP database has an **8-hour target RTO**, while its dependent ERP application has a **4-hour target RTO**. This prompts review of objective alignment; it does not prove an actual recovery failure.
- Office project coordination has no recorded accountable owner.

## How the model works

A service’s `depends_on` list names its hard prerequisites. If B depends on A, the model records **B → A**. Impact analysis traverses reverse edges from A to potentially affected consumers.

- **Impact:** breadth-first search returns unique downstream services and one deterministic shortest explanation path per service.
- **Cycles:** Tarjan’s strongly connected components algorithm finds circular groups, including self-dependencies.
- **Validation waves:** a topological pass groups target services and prerequisite closure into ordered waves. Cycles and services blocked by cycles remain unresolved.
- **Concentration ranking:** potentially affected business workflows, then downstream-service count, with stable ID tie-breaking. This is not a financial risk score.

Selected roots are excluded from downstream counts. Business-workflow counts include a selected root if its `kind` is `business`. Owner counts represent distinct recorded owner strings for the root and its downstream services; they do not count staff.

Validation waves include healthy prerequisites so they can be checked before dependent recovery. They are not timed restoration steps. RTO values are declared recovery objectives, not measured task durations, and the program never adds them together to predict downtime.

## Inventory schema

```json
{
  "schema_version": 1,
  "title": "Example inventory",
  "services": [
    {
      "id": "network",
      "name": "Office network",
      "kind": "infrastructure",
      "owner": "IT",
      "site": "Office",
      "purpose": "Internal connectivity",
      "rto_hours": 2,
      "depends_on": []
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `id` | Unique lowercase slug, starting with a letter; maximum 64 characters |
| `name` | Nonempty display name |
| `kind` | `infrastructure`, `application`, or `business` |
| `owner` | Accountable role/group; empty values create a review finding |
| `site` | Location description; empty values create a review finding |
| `purpose` | Operational purpose; empty values create a review finding |
| `rto_hours` | Positive finite recovery-time objective; not measured recovery time |
| `depends_on` | IDs of hard prerequisites; no duplicate edges or unknown IDs |

The tool accepts up to 200 services and a 2 MB inventory. Invalid JSON, duplicate keys or IDs, and invalid field types are rejected. Cycles are allowed as input so the tool can report them. There are no network calls, credential collection, or infrastructure changes.

## Tests and implementation boundaries

25 tests cover chain and diamond graphs, directionality, duplicate counting, isolated services, cycles and self-loops, validation order, RTO comparisons, missing owners, deterministic results, malformed input, safe HTML data embedding, sample outcomes, CLI exit codes, and output protection.

The HTML report uses native browser controls, visible focus indicators, responsive layouts, and text-based dependency explanations. User-provided inventory values are inserted as text; embedded JSON escapes script-terminating characters. No external fonts, scripts, analytics, or libraries are loaded.

## Limitations

This is an inventory-based planning tool, not live discovery, monitoring, or outage prediction. It does not model optional dependencies, partial degradation, redundant paths, failover success, cached sessions, recovery task durations, staffing constraints, or financial loss. A transitive dependency is a reason to investigate potential impact, not a confirmed outage.

Use fictional or properly sanitized data for public demonstrations. Validate a real model with service owners and recovery exercises before relying on it operationally.

## Files

- `analyzer.py`: graph analysis, validation, CLI, and report generation.
- `report-template.html`: offline report interface.
- `examples/`: fictional inputs and generated report snapshots.
- `tests/`: standard-library test suite.
- `.github/workflows/test.yml`: Python test matrix.
- `DEMO_GUIDE.md`: a short demonstration and explanation guide.
- `GITHUB_SETUP.md`: publication steps.
