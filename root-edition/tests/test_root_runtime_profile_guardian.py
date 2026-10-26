import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"runtime"))
import unittest
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import Mock
from profile_guardian import watch


class GuardianTests(unittest.TestCase):
    def test_detached_process_writes_ready_and_runs_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            script='''
import json, os, sys, time
from pathlib import Path
import guardian_device as g
g.d.STATE=Path(sys.argv[1]); g.d.EXPECTED_UID=os.geteuid()
j={'transaction':'fixture','state':'pending','deadline':time.monotonic()+0.2}
g.d.save(j)
def restore(tx):
    (g.d.STATE/'recovered').write_text(tx)
    return 'restored'
g.restore=restore
assert g.run('fixture')=='restored'
'''
            child=subprocess.Popen([sys.executable,'-c',script,tmp],cwd=Path(__file__).resolve().parents[1]/"runtime",
                                   stdin=subprocess.DEVNULL,start_new_session=True)
            self.assertEqual(child.wait(timeout=5),0)
            self.assertTrue((Path(tmp)/'profile-guardian-ready.json').exists())
            self.assertEqual((Path(tmp)/'recovered').read_text(),'fixture')

    def run_watch(self, journal, tx='trial', now=100):
        clock=[now]; ready=Mock(); restore=Mock(return_value='restored')
        def sleep(seconds): clock[0]+=seconds
        result=watch(tx,lambda: journal, ready, restore, lambda:clock[0],sleep)
        return result,ready,restore,clock[0]

    def test_recovers_only_at_deadline_and_binds_transaction(self):
        result,ready,restore,end=self.run_watch({'transaction':'trial','state':'pending','deadline':145})
        self.assertEqual(result,'restored'); self.assertEqual(end,145)
        ready.assert_called_once_with('trial',145)
        restore.assert_called_once_with('trial')

    def test_old_timer_never_recovers_new_trial(self):
        result,ready,restore,_=self.run_watch({'transaction':'new','state':'pending','deadline':145})
        self.assertEqual(result,'superseded'); ready.assert_not_called(); restore.assert_not_called()

    def test_terminal_journal_never_rearms(self):
        for state in ('restored','conflict'):
            result,ready,restore,_=self.run_watch({'transaction':'trial','state':state,'deadline':145})
            self.assertEqual(result,state); ready.assert_not_called(); restore.assert_not_called()

    def test_invalid_deadline_never_acknowledges_readiness(self):
        for deadline in (float('nan'),float('inf'),True,191,'145',None):
            with self.subTest(deadline=deadline), self.assertRaises(ValueError):
                self.run_watch({'transaction':'trial','state':'pending','deadline':deadline})

    def test_expired_deadline_recovers_immediately(self):
        result,ready,restore,end=self.run_watch({'transaction':'trial','state':'pending','deadline':99})
        self.assertEqual(result,'restored'); self.assertEqual(end,100)
        ready.assert_not_called(); restore.assert_called_once_with('trial')


if __name__ == '__main__': unittest.main()

class PromotionGuardianTests(unittest.TestCase):
    def test_confirmed_continuation_is_guarded_instead_of_expiring(self):
        now=[100];recovered=[];continuations=[]
        def continuation():
            continuations.append(now[0])
            if now[0]>=101:return 'lease-expired'
        result=watch('t',lambda:dict(transaction='t',state='pending',deadline=160),
                     lambda *a:None,recovered.append,lambda:now[0],
                     lambda n:now.__setitem__(0,now[0]+n),continuation=continuation)
        self.assertEqual(result,'lease-expired');self.assertFalse(recovered)
        self.assertLess(now[0],160)
