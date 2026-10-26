import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"runtime"))
import copy
import unittest
from profile_plan import STOCK, CANDIDATE, snapshot
from profile_recovery import prepare, recover
from test_root_runtime_profile_plan import response


class Model:
    def __init__(self):
        self.reply = response(CANDIDATE, CANDIDATE)
        self.sam = CANDIDATE
        self.file = 'owned'
        self.refresh_error = False
        self.refresh_stale = False
        self.read_error = False
        self.write_lost = False
        self.events = []
        self.saved = []

    def remove(self):
        self.events.append('remove')
        if self.file == 'foreign': return 'conflict'
        self.file = None
        return 'absent'

    def refresh(self):
        self.events.append('refresh')
        if not self.refresh_stale: self.reply = response()
        if self.refresh_error: raise TimeoutError('Reply lost')

    def read(self):
        self.events.append('read')
        if self.read_error: raise TimeoutError('Unavailable')
        return snapshot(self.reply, self.sam)

    def write(self, target):
        self.events.append('write')
        self.sam = target
        if self.write_lost: raise TimeoutError('Reply lost after write')

    def save(self, journal):
        self.events.append('save:'+journal['state'])
        self.saved.append(copy.deepcopy(journal))


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.j = prepare(response(), STOCK)
        self.m = Model()

    def run_recovery(self):
        m = self.m
        return recover(self.j, m.remove, m.refresh, m.read, m.write, m.save)

    def test_complete_recovery_is_read_back(self):
        self.assertEqual(self.run_recovery(), 'restored')
        self.assertEqual(self.m.events[0], 'save:recovering')
        self.assertEqual(self.m.events[-2:], ['read', 'save:restored'])

    def test_refresh_reply_lost_but_readback_passes(self):
        self.m.refresh_error = True
        self.assertEqual(self.run_recovery(), 'restored')

    def test_stale_profiles_remain_pending_even_if_sam_restored(self):
        self.m.refresh_stale = True
        self.assertEqual(self.run_recovery(), 'recovering')
        self.assertEqual(self.m.sam, STOCK)

    def test_resume_after_file_removed_and_failed_read(self):
        self.m.read_error = True
        self.assertEqual(self.run_recovery(), 'recovering')
        self.assertIsNone(self.m.file)
        self.j = copy.deepcopy(self.m.saved[-1])
        self.m.read_error = False
        self.assertEqual(self.run_recovery(), 'restored')

    def test_foreign_file_is_preserved_without_rescan(self):
        self.m.file = 'foreign'
        self.assertEqual(self.run_recovery(), 'conflict')
        self.assertEqual(self.m.file, 'foreign')
        self.assertNotIn('refresh', self.m.events)

    def test_foreign_sam_is_not_overwritten(self):
        self.m.sam = 'other.home'
        self.assertEqual(self.run_recovery(), 'conflict')
        self.assertNotIn('write', self.m.events)

    def test_lost_sam_write_reply_is_checked(self):
        self.m.write_lost = True
        self.assertEqual(self.run_recovery(), 'restored')

    def test_invalid_journal_rejected_before_side_effects(self):
        for key, value in [('armed', False), ('payload_sha256', 'wrong'), ('state', 'unknown')]:
            self.j = prepare(response(), STOCK)
            self.j[key] = value
            with self.assertRaises(ValueError): self.run_recovery()
        self.assertEqual(self.m.events, [])

    def test_failed_journal_save_prevents_removal(self):
        def fail(_): raise OSError('disk full')
        with self.assertRaises(OSError):
            recover(self.j, self.m.remove, self.m.refresh, self.m.read, self.m.write, fail)
        self.assertEqual(self.m.events, [])

    def test_finished_journal_does_not_rearm(self):
        self.assertEqual(self.run_recovery(), 'restored')
        self.m.events.clear()
        self.assertEqual(self.run_recovery(), 'restored')
        self.assertEqual(self.m.events, [])

    def test_failed_final_save_does_not_mark_memory_restored(self):
        def fail_final(j):
            if j['state'] == 'restored': raise OSError('disk full')
            self.m.save(j)
        with self.assertRaises(OSError):
            recover(self.j, self.m.remove, self.m.refresh, self.m.read, self.m.write, fail_final)
        self.assertEqual(self.j['state'], 'recovering')
        self.assertEqual(self.run_recovery(), 'restored')


if __name__ == '__main__': unittest.main()
