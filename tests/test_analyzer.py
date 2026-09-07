import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from analyzer import Model, validate, load_inventory, markdown, html_report, main


def service(key, deps=(), **overrides):
    return dict(id=key,name=key,owner='IT',site='Office',purpose='Sample',kind='application',rto_hours=4,depends_on=list(deps)) | overrides

def model(*rows):
    return Model({'schema_version':1,'title':'Test inventory','services':list(rows)})


class GraphTests(unittest.TestCase):
    def test_chain_impact_direction(self):
        m=model(service('a'),service('b',['a']),service('c',['b']))
        self.assertEqual(m.impact('a')['affected'],['b','c'])
        self.assertEqual(m.impact('a')['paths']['c'],['a','b','c'])
        self.assertEqual(m.impact('c')['affected'],[])
    def test_diamond_counts_once(self):
        m=model(service('a'),service('b',['a']),service('c',['a']),service('d',['b','c']))
        self.assertEqual(m.impact('a')['affected'],['b','c','d'])
        self.assertEqual(len(m.impact('a')['paths']['d']),3)
    def test_disconnected_service_excluded(self):
        m=model(service('a'),service('b',['a']),service('z'))
        self.assertEqual(m.impact('a')['affected'],['b'])
    def test_cycle_and_dependent_are_unresolved(self):
        m=model(service('a',['b']),service('b',['a']),service('c',['b']),service('d'))
        self.assertEqual(m.cycles(),[['a','b']])
        self.assertEqual(m.impact('a')['prerequisite_plan']['unresolved'],['a','b','c'])
    def test_self_loop(self):
        m=model(service('a',['a']))
        self.assertEqual(m.cycles(),[['a']])
        self.assertEqual(m.impact('a')['affected'],[])
    def test_validation_waves_include_healthy_prerequisites(self):
        m=model(service('a'),service('healthy'),service('b',['a','healthy']),service('c',['b']))
        s=m.impact('a')
        self.assertNotIn('healthy',s['affected'])
        self.assertEqual(s['prerequisite_plan']['waves'],[['a','healthy'],['b'],['c']])
    def test_target_rto_alignment_warning(self):
        m=model(service('a',rto_hours=8),service('b',['a'],rto_hours=4))
        self.assertEqual(m.report()['findings'][0]['code'],'RTO_ALIGNMENT_REVIEW')
    def test_equal_targets_do_not_warn(self):
        self.assertEqual(model(service('a'),service('b',['a'])).report()['findings'],[])
    def test_missing_owner_flagged(self):
        self.assertEqual(model(service('a',owner=' ')).report()['findings'][0]['code'],'MISSING_OWNER')
    def test_business_root_is_counted(self):
        self.assertEqual(model(service('payroll',kind='business')).impact('payroll')['business_services'],['payroll'])
    def test_order_independence(self):
        a=service('a');b=service('b',['a']);c=service('c',['a'])
        self.assertEqual(model(a,b,c).report(),model(c,b,a).report())
    def test_unknown_dependency_rejected(self):
        with self.assertRaisesRegex(ValueError,'unknown dependency'):model(service('a',['missing']))
    def test_duplicate_service_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate service'):model(service('a'),service('a'))
    def test_duplicate_edge_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate dependencies'):model(service('a'),service('b',['a','a']))
    def test_invalid_recovery_target(self):
        for value in [True,0,-2,float('nan'),float('inf'),'4']:
            with self.subTest(value=value),self.assertRaises(ValueError):model(service('a',rto_hours=value))
    def test_payload_cannot_close_embedded_script(self):
        payload='</script><img src=x onerror=alert(1)>'
        report=model(service('a',name=payload)).report()
        rendered=html_report(report)
        self.assertNotIn(payload,rendered)
        self.assertIn('\\u003c/script\\u003e',rendered)
    def test_unknown_scenario(self):
        with self.assertRaises(ValueError):model(service('a')).impact('missing')
    def test_sample_office_outage(self):
        m=Model(load_inventory('examples/construction-services.json'))
        s=m.impact('office-internet')
        self.assertEqual(set(s['business_services']),{'collaboration','dispatch','timecards'})
        self.assertNotIn('payroll',s['affected'])
        self.assertEqual(len(s['affected']),6)
    def test_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.json';p.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaisesRegex(ValueError,'Duplicate JSON key'):load_inventory(p)
    def test_markdown_report_paths(self):
        report=model(service('a'),service('b',['a'])).report()
        self.assertIn('a → b',markdown(report,'a'))
    def test_cli_writes_report_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'report.json'
            args=['examples/construction-services.json','--format','json','--output',str(p)]
            with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(main(args),0)
            self.assertEqual(len(json.loads(p.read_text())['inventory']['services']),16)
            with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(main(args),2)
            with contextlib.redirect_stdout(io.StringIO()):self.assertEqual(main(args+['--overwrite']),0)
    def test_cli_findings_policy(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['examples/construction-services.json','--fail-on-findings']),1)
    def test_cli_cannot_overwrite_inventory(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['examples/construction-services.json','--output','examples/construction-services.json','--overwrite']),2)
    def test_cli_rejects_ignored_scenario_option(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['examples/construction-services.json','--format','json','--service','dns']),2)
    def test_size_bound(self):
        rows=[service('s'+str(i)) for i in range(201)]
        with self.assertRaises(ValueError):model(*rows)

if __name__=='__main__':unittest.main()
