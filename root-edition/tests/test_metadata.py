import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import metadata as m

RAW=b'{ "id":"com.gathin.tvhome", "type":"web", "main":"index.html", "version":"1.1.0", "needNetworkToLaunchOnBoot":false, "extra":{"keep":[1,2]} }\n'

class MetadataTests(unittest.TestCase):
    def test_changes_only_category_and_restores_exact_bytes(self):
        j=m.prepare(RAW)
        candidate=base64.b64decode(j['candidate_b64'])
        expected=json.loads(RAW);expected['appCategory']=['home']
        self.assertEqual(json.loads(candidate),expected)
        self.assertEqual(m.recovery(candidate,j),RAW)
        self.assertIsNone(m.recovery(RAW,j))

    def test_numeric_tokens_are_not_rounded_or_normalized(self):
        raw=RAW.replace(b'"extra":{"keep":[1,2]}',b'"extra":{"decimal":0.12345678901234567890,"huge":1e999,"negativeZero":-0,"integer":123456789012345678901234567890}')
        candidate=base64.b64decode(m.prepare(raw)['candidate_b64'])
        for token in (b'0.12345678901234567890',b'1e999',b'-0',b'123456789012345678901234567890'):
            self.assertIn(token,candidate)
        self.assertEqual(m.recovery(candidate,m.prepare(raw)),raw)

    def test_existing_categories_preserved(self):
        value=json.loads(RAW);value['appCategory']=['media','custom']
        j=m.prepare(json.dumps(value).encode())
        self.assertEqual(json.loads(base64.b64decode(j['candidate_b64']))['appCategory'],['media','custom','home'])

    def test_already_home_is_byte_identical(self):
        raw=RAW.replace(b'"type":"web"',b'"appCategory":["home"],"type":"web"')
        j=m.prepare(raw)
        self.assertFalse(j['change_required'])
        self.assertEqual(base64.b64decode(j['candidate_b64']),raw)

    def test_invalid_inputs(self):
        invalid=[b'{}',b'[]',b'null',b'\xff',RAW.replace(b'com.gathin.tvhome',b'com.webos.app.home'),
                 RAW.replace(b'"type":"web"',b'"type":"native"'),
                 RAW.replace(b'"type":"web"',b'"type":"web","type":"native"'),
                 RAW.replace(b'"type":"web"',b'"type":"web","appCategory":null'),
                 RAW.replace(b'"type":"web"',b'"type":"web","appCategory":[5]'),
                 RAW.replace(b'"type":"web"',b'"type":"web","x":NaN'),b' '*65537]
        for raw in invalid:
            with self.subTest(raw=raw[:80]),self.assertRaises(ValueError):m.prepare(raw)

    def test_foreign_edit_preserved(self):
        j=m.prepare(RAW)
        with self.assertRaises(m.Conflict): m.recovery(RAW+b' ',j)

    def test_tampered_journal_rejected(self):
        j=m.prepare(RAW)
        for key,value in [('original_sha256','bad'),('candidate_sha256','bad'),('version',2),('version',True),('change_required',1),
                          ('original_b64','!'),('candidate_b64',j['original_b64']),('change_required',False)]:
            bad=copy.deepcopy(j);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.recovery(RAW,bad)

    def test_rehashed_unrelated_mutation_rejected(self):
        j=m.prepare(RAW)
        candidate=json.loads(base64.b64decode(j['candidate_b64']));candidate['main']='other.js'
        raw=json.dumps(candidate).encode()
        j['candidate_b64']=base64.b64encode(raw).decode();j['candidate_sha256']=m.digest(raw)
        with self.assertRaises(ValueError):m.recovery(raw,j)

    def test_cli_does_not_modify_input_or_overwrite_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);src=p/'appinfo.json';dst=p/'plan.json';src.write_bytes(RAW)
            command=[sys.executable,str(Path(m.__file__)),'--input',str(src),'--output',str(dst)]
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
            first=dst.read_bytes()
            self.assertEqual(dst.stat().st_mode & 0o777,0o600)
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
            self.assertEqual(src.read_bytes(),RAW);self.assertEqual(dst.read_bytes(),first)

if __name__=='__main__':unittest.main()
