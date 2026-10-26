"""Semantic desktop bridge; TV work never runs on the UI thread."""
import queue
import re
from dataclasses import dataclass, field

from .terminal import Console


@dataclass(repr=False)
class Prompt:
    label: str
    options: list = field(default_factory=list)
    secret: bool = False

    @property
    def kind(self):
        if self.secret:
            return 'secret'
        if re.search(r'\[[Yy]/[Nn]\]', self.label):
            return 'confirm'
        if self.options:
            return 'choice'
        if 'Private key file' in self.label:
            return 'file'
        if 'Press Enter' in self.label:
            return 'ready'
        return 'text'

    @property
    def default(self):
        if self.kind == 'confirm':
            return 'y' if '[Y/n]' in self.label else 'n'
        match = re.search(r'\[(\d+)\]', self.label)
        return match.group(1) if match else ''

    @property
    def title(self):
        return re.sub(r'\s*\[[^]]+\]', '', self.label).strip().rstrip(':')


class DesktopConsole(Console):
    def __init__(self, emit):
        self.emit = emit
        self.options = []
        self.color = self.interactive = False
        self.raw = lambda text: emit('text', str(text).strip())

    def text(self, message, bold=False):
        message = str(message).strip()
        # These are keyboard instructions for the terminal, represented by controls here.
        if (not message or ' = ' in message or message.startswith(('q / Ctrl+C', 'Typing is hidden:', 'TV > Edition'))):
            return
        self.emit('text', message)

    def heading(self, title):
        self.emit('heading', title)

    def error(self, message, heading=False):
        self.emit('error-heading' if heading else 'error', message)

    def step(self, number, title, clear=True):
        self.options = []
        self.emit('step', (number, title, clear))

    def option(self, key, label, detail=''):
        self.options.append((str(key), label, detail))

    def prompt(self, text):
        return text

    def reader(self, ask):
        return ask


class Channel:
    def __init__(self, emit):
        self.emit = emit
        self.console = DesktopConsole(emit)
        self.answers = queue.Queue()

    def answer(self, value):
        self.answers.put(value)

    def ask(self, label, secret=False):
        options, self.console.options = self.console.options, []
        self.emit('prompt', Prompt(label, [] if secret else options, secret))
        value = self.answers.get()
        if value is None:
            raise EOFError
        return value

    def secret(self, label):
        return self.ask(label, secret=True)
