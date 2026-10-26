import importlib.util
from pathlib import Path
import unittest
s=importlib.util.spec_from_file_location('doctor',Path(__file__).parents[1]/'doctor.py')
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
class DoctorTests(unittest.TestCase):
 def test_nonroot(self):
  r=d.parse('uid=1000\nkernel_arch=aarch64\nuserspace_bits=32\n')
  self.assertEqual(r['root_status'],'NOT_ROOT_IN_THIS_SESSION')
  self.assertEqual(r['observations']['userspace_bits'],'32')
 def test_uid_zero_is_not_host_root_proof(self):
  self.assertEqual(d.parse('uid=0\n')['root_status'],'UID_ZERO_CONTEXT_UNVERIFIED')
 def test_missing_uid(self):
  self.assertEqual(d.parse('uid=bad\n')['root_status'],'UNKNOWN')
 def test_private_and_control_data_removed(self):
  r=d.parse('serial=secret\npassword=secret\nkernel_arch=arm\x1b[31m\n')
  self.assertNotIn('secret',str(r));self.assertNotIn('kernel_arch',r['observations'])
 def test_no_ready_claim(self):
  r=d.parse('uid=0\nfirmware=43.21.71\n')
  self.assertEqual(r['integration_status'],'NO_VALIDATED_ADAPTER')
  self.assertEqual(r['rootability'],'NOT_DETERMINED_BY_PROBE')
 def test_duplicate_rejected(self):
  with self.assertRaises(ValueError):d.parse('uid=0\nuid=1000\n')
 def test_ssh_destination(self):
  for bad in ['-oProxyCommand=bad','host;bad','a b','a\nb']:
   with self.assertRaises(ValueError):d.destination(bad)
  self.assertEqual(d.destination('prisoner@192.0.2.1'),'prisoner@192.0.2.1')
class SystemInfoTests(unittest.TestCase):
 def test_allowlisted_system_info(self):
  r=d.parse('uid=5999\n')
  d.add_system_info(r, '{"returnValue":true,"modelName":"OLED55C3RLA","firmwareVersion":"43.21.71","sdkVersion":"11.2.0","serial":"secret"}')
  self.assertEqual(r['observations']['firmwareVersion'],'43.21.71')
  self.assertNotIn('secret',str(r))
 def test_failed_query_not_accepted(self):
  with self.assertRaises(ValueError):d.add_system_info({}, '{"returnValue":false}')
 def test_wrong_type_not_accepted(self):
  with self.assertRaises(ValueError):d.add_system_info({}, '[]')


class AppInfoTests(unittest.TestCase):
 def test_missing_category_is_a_gate(self):
  r=d.parse('uid=0\n')
  d.add_app_info(r, '{"returnValue":true,"appInfo":{"id":"com.gathin.tvhome","version":"1.1.0","type":"web","folderPath":"private"}}')
  self.assertEqual(r['launcher']['home_category'],'MISSING')
  self.assertNotIn('private',str(r))
  self.assertEqual(r['integration_status'],'NO_VALIDATED_ADAPTER')
 def test_category_is_not_installation_approval(self):
  r=d.parse('uid=0\n')
  d.add_app_info(r, '{"returnValue":true,"appInfo":{"id":"com.gathin.tvhome","version":"1.1.0","type":"web","appCategory":["home"]}}')
  self.assertEqual(r['launcher']['home_category'],'REGISTERED')
  self.assertEqual(r['integration_status'],'NO_VALIDATED_ADAPTER')
 def test_wrong_app_and_failed_query_rejected(self):
  for raw in ['{"returnValue":false}', '{"returnValue":true,"appInfo":{"id":"other"}}','[]']:
   with self.assertRaises(ValueError):d.add_app_info({},raw)

if __name__=='__main__':unittest.main()
