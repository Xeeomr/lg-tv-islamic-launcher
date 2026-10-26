"""Desktop adapters must preserve CLI choices, cancellation and secret privacy."""
import queue
import threading
import unittest
from cytv.desktop import DesktopConsole, Prompt, Channel


class DesktopTests(unittest.TestCase):
    def test_error_events_are_distinct_from_progress(self):
        events = []
        console = DesktopConsole(lambda *event: events.append(event))
        console.error('Could not complete this step', heading=True)
        console.error('Failure details')
        console('Normal progress')
        self.assertEqual(events, [('error-heading', 'Could not complete this step'),
                                  ('error', 'Failure details'), ('text', 'Normal progress')])

    def test_semantic_output_keeps_long_diagnostic_path_intact(self):
        events = []
        console = DesktopConsole(lambda *event: events.append(event))
        path = '/some very long folder/' + 'a' * 100 + '.json'
        console.heading('Attach this diagnostic report')
        console.raw(path)
        self.assertEqual(events[-1], ('text', path))
        self.assertEqual(events[0], ('heading', 'Attach this diagnostic report'))

    def test_choice_values_include_zero_and_recommended_default(self):
        prompt = Prompt('TV number [1]: ', [('1', 'Living room', '192.168.1.2'), ('0', 'Add another TV', '')])
        self.assertEqual(prompt.kind, 'choice')
        self.assertEqual(prompt.default, '1')
        self.assertEqual(prompt.options[-1][0], '0')

    def test_destructive_default_is_no(self):
        self.assertEqual(Prompt('Continue [y/N]: ').default, 'n')
        self.assertEqual(Prompt('Connect and remember this TV? [Y/n]: ').default, 'y')

    def test_password_never_becomes_choice(self):
        self.assertEqual(Prompt('Password: ', [('1', 'old option', '')], secret=True).kind, 'secret')

    def test_cancel_unblocks_waiting_worker(self):
        events, outcome = queue.Queue(), []
        channel = Channel(lambda *event: events.put(event))
        def run():
            try:
                channel.ask('TV IP address: ')
            except EOFError:
                outcome.append('cancelled')
        worker = threading.Thread(target=run)
        worker.start()
        self.assertEqual(events.get(timeout=2)[0], 'prompt')
        channel.answer(None)
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(outcome, ['cancelled'])

    def test_choices_do_not_leak_to_next_prompt(self):
        events = queue.Queue()
        channel = Channel(lambda *event: events.put(event))
        channel.console.option(1, 'Root')
        channel.answer('1')
        self.assertEqual(channel.ask('Edition [1]: '), '1')
        channel.answer('secret')
        self.assertEqual(channel.secret('Password: '), 'secret')
        prompts = []
        while not events.empty():
            event = events.get_nowait()
            if event[0] == 'prompt':
                prompts.append(event[1])
        self.assertEqual(prompts[1].options, [])
        self.assertNotIn('secret', repr(prompts))
