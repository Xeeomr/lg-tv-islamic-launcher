"""Windowed cytv wizard. Run with python -m cytv.gui."""
import html
from pathlib import Path
import shutil
import sys
import threading

from PySide6.QtCore import QObject, Signal, QUrl, QTimer, Qt
from PySide6.QtGui import QDesktopServices, QIcon, QFontDatabase, QFont
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout,
                              QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar,
                              QPushButton, QTextBrowser, QVBoxLayout, QWidget, QButtonGroup)

from cytv import __version__, cli, diagnostics, i18n
from cytv.i18n import translate as tr
from cytv.desktop import Channel
from cytv.gui_style import STYLE, TVPreview, Select, EditionOption, BrandSignature

MAINTENANCE_ACTIONS = (
    ('Check TV status', 'status'),
    ('Check connection and create a diagnostic report', 'doctor'),
    ('Return to LG Home', 'restore'),
    ('Uninstall Clean Your TV', 'uninstall'),
    ('Home button diagnostics', 'home-diagnostics'),
    ('Enable updates for all TV components (root required)', 'enable-system-updates'),
)


class Events(QObject):
    event = Signal(str, object)


class Wizard(QMainWindow):
    def __init__(self, run=cli.main):
        super().__init__()
        i18n.configure()
        self.run = run
        self.running = False
        self.pending = None
        self.report = None
        self.worker = None
        self.setWindowTitle('Clean Your TV')
        self.resize(1060, 820)
        self.setMinimumSize(900, 680)
        self.setStyleSheet(STYLE)
        self.current_step = 0
        self.command = 'install'
        self.events = Events()
        self.events.event.connect(self.receive)
        body = QWidget()
        self.setCentralWidget(body)
        shell = QHBoxLayout(body)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(248)
        rail = QVBoxLayout(sidebar)
        rail.setContentsMargins(20, 24, 20, 26)
        rail.setSpacing(8)
        self.brand = BrandSignature(cli.payload_dir() / 'brand-stacked.svg')
        rail.addWidget(self.brand)
        rail.addSpacing(12)
        self.rail_title = QLabel()
        self.rail_title.setObjectName('railTitle')
        self.rail_title.setWordWrap(True)
        rail.addWidget(self.rail_title)
        rail.addSpacing(12)
        self.steps = QWidget()
        step_layout = QVBoxLayout(self.steps)
        step_layout.setContentsMargins(0, 0, 0, 0)
        step_layout.setSpacing(12)
        self.step_rows = []
        self.step_names = []
        self.step_numbers = []
        for number in range(1, 5):
            row = QFrame()
            row.setObjectName('step')
            line = QHBoxLayout(row)
            line.setContentsMargins(10, 12, 10, 12)
            line.setSpacing(12)
            marker = QLabel(str(number))
            marker.setObjectName('stepNumber')
            marker.setFixedSize(32, 32)
            marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name = QLabel()
            name.setObjectName('stepName')
            name.setWordWrap(True)
            line.addWidget(marker)
            line.addWidget(name, 1)
            self.step_rows.append(row)
            self.step_names.append(name)
            self.step_numbers.append(marker)
            step_layout.addWidget(row)
        rail.addWidget(self.steps)
        rail.addStretch()
        self.rail_note = QLabel()
        self.rail_note.setObjectName('railNote')
        self.rail_note.setWordWrap(True)
        rail.addWidget(self.rail_note)
        rail.addSpacing(20)
        version = QLabel('cytv ' + __version__)
        version.setObjectName('version')
        rail.addWidget(version)
        shell.addWidget(sidebar)
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(40, 30, 40, 24)
        layout.setSpacing(12)
        header = QHBoxLayout()
        self.badge = QLabel()
        self.badge.setObjectName('badge')
        header.addWidget(self.badge)
        header.addStretch()
        self.language = Select()
        self.language.setObjectName('language')
        self.language.setAccessibleName(tr('Language'))
        for code, name in i18n.LANGUAGES.items():
            self.language.addItem(tr(name) if code == 'auto' else name, code)
        self.language.setCurrentIndex(list(i18n.LANGUAGES).index(i18n.language_choice()))
        self.language.currentIndexChanged.connect(self.change_language)
        header.addWidget(self.language)
        layout.addLayout(header)
        layout.addSpacing(18)
        self.title = QLabel()
        self.title.setObjectName('title')
        self.title.setWordWrap(True)
        layout.addWidget(self.title)
        self.subtitle = QLabel()
        self.subtitle.setObjectName('subtitle')
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.subtitle)
        self.preview = TVPreview()
        layout.addWidget(self.preview)
        self.content = QTextBrowser()
        self.content.setOpenExternalLinks(False)
        self.content.setFrameShape(QFrame.Shape.NoFrame)
        self.content.document().setDefaultStyleSheet(
            'p { margin-top: 6px; margin-bottom: 12px; line-height: 140%; } '
            'h3 { color: #f3ede3; font-size: 16px; margin-top: 12px; margin-bottom: 10px; }')
        layout.addWidget(self.content, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.form = QWidget()
        self.form.setObjectName('form')
        self.form_layout = QVBoxLayout(self.form)
        self.form_layout.setContentsMargins(16, 16, 16, 16)
        self.form_layout.setSpacing(10)
        layout.addWidget(self.form)
        footer = QHBoxLayout()
        footer.addStretch()
        self.cancel = QPushButton(tr('Close'))
        self.cancel.setObjectName('close')
        self.cancel.clicked.connect(self.close)
        footer.addWidget(self.cancel)
        layout.addLayout(footer)
        shell.addWidget(main, 1)
        self.home()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'preview'):
            self.preview.setFixedHeight(144 if self.height() < 760 else 206)

    def change_language(self):
        if self.running:
            return
        previous = i18n.language_choice()
        try:
            i18n.configure(self.language.currentData())
        except OSError:
            self.language.blockSignals(True)
            self.language.setCurrentIndex(list(i18n.LANGUAGES).index(previous))
            self.language.blockSignals(False)
            self.error_dialog('Could not save language preference', 'Check write access to the application data folder and try again.')
            return
        self.language.setAccessibleName(tr('Language'))
        self.language.setItemText(0, tr('Auto'))
        self.cancel.setText(tr('Close'))
        self.home()

    def clear_form(self):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def button(self, label, callback, default=False):
        button = QPushButton(tr(label))
        button.setMinimumHeight(44)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setDefault(default)
        button.setProperty('primary', default)
        button.clicked.connect(callback)
        self.form_layout.addWidget(button)
        return button

    def update_steps(self, number=0, result=None):
        self.current_step = number
        for index, row in enumerate(self.step_rows, 1):
            state = 'complete' if index < number else 'current' if index == number else 'upcoming'
            if result == 0:
                state = 'complete'
            elif index == number and result is not None:
                state = 'error' if result != 130 else 'upcoming'
            row.setProperty('state', state)
            self.step_numbers[index - 1].setText('✓' if state == 'complete' else '!' if state == 'error' else str(index))
            row.style().unpolish(row)
            row.style().polish(row)
            for label in (self.step_numbers[index - 1], self.step_names[index - 1]):
                label.style().unpolish(label)
                label.style().polish(label)
            row.update()

    def set_error_state(self, failed):
        for widget in (self.title, self.badge):
            widget.setProperty('state', 'error' if failed else '')
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def error_dialog(self, title, message):
        dialog = QMessageBox(QMessageBox.Icon.Warning, tr(title), tr(message), parent=self)
        dialog.setStyleSheet('QLabel { color: #ff6b6b; }')
        dialog.exec()

    def home(self):
        self.clear_form()
        self.preview.show()
        self.subtitle.show()
        self.steps.show()
        self.progress.hide()
        self.update_steps()
        self.set_error_state(False)
        self.badge.setText(tr('Before you begin'))
        self.rail_title.setText(tr('Set up my TV'))
        self.rail_note.setText(tr('Keep your TV on and watch for a pairing request.'))
        for label, title in zip(self.step_names, ('Connect to your TV', 'Choose your edition', 'Prepare the TV connection', 'Review and install')):
            label.setText(tr(title))
        self.title.setText(tr('Make your TV feel like yours'))
        self.subtitle.setText(tr('Install Root or No-root. We will help you choose.'))
        self.content.setHtml('<h3>' + html.escape(tr('Before you begin')) + '</h3><p>' + html.escape(tr('Turn on your LG webOS TV and connect it to the same home network as this computer.')) + '</p><p>' + html.escape(tr('cytv will look for your TV automatically. Keep the remote nearby to approve pairing on the TV.')) + '</p>')
        self.button('Set up my TV', lambda: self.start('install'), True)
        self.maintenance_toggle = self.button('Maintenance action', self.toggle_maintenance)
        self.maintenance_toggle.setObjectName('maintenanceToggle')
        self.maintenance_toggle.setCheckable(True)
        self.maintenance_toggle.setText(tr('Maintenance action') + '  ▸')
        self.maintenance = QWidget()
        maintenance_layout = QVBoxLayout(self.maintenance)
        maintenance_layout.setContentsMargins(0, 0, 0, 0)
        maintenance_layout.setSpacing(10)
        actions = Select()
        actions.setAccessibleName(tr('Maintenance action'))
        for label, command in MAINTENANCE_ACTIONS:
            actions.addItem(tr(label), command)
        maintenance_layout.addWidget(actions)
        execute = QPushButton(tr('Run selected maintenance action'))
        execute.setMinimumHeight(44)
        execute.clicked.connect(lambda: self.start(actions.currentData()))
        maintenance_layout.addWidget(execute)
        self.form_layout.addWidget(self.maintenance)
        self.maintenance.hide()

    def toggle_maintenance(self):
        expanded = self.maintenance_toggle.isChecked()
        self.maintenance.setVisible(expanded)
        self.maintenance_toggle.setText(tr('Maintenance action') + ('  ▾' if expanded else '  ▸'))

    def start(self, command):
        if self.running:
            return
        self.running = True
        self.set_error_state(False)
        self.command = command
        self.operation_title = next((label for label, key in MAINTENANCE_ACTIONS if key == command), 'Set up my TV')
        self.preview.hide()
        self.subtitle.show()
        self.steps.setVisible(command == 'install')
        self.update_steps(1)
        self.badge.setText(tr('Connecting to your TV' if command == 'install' else 'Maintenance action'))
        if command != 'install':
            self.rail_title.setText(tr(self.operation_title))
        self.language.setEnabled(False)
        self.report = None
        self.pending = None
        self.content.clear()
        self.clear_form()
        self.title.setText(tr('Connecting to your TV' if command == 'install' else self.operation_title))
        self.subtitle.setText(tr('Keep your TV on and watch for a pairing request.'))
        self.cancel.setText(tr('Cancel'))
        self.cancel.setEnabled(False)
        self.progress.show()
        self.channel = Channel(self.events.event.emit)
        def work():
            try:
                args = [command, '--report'] if command == 'doctor' else [command]
                args += ['--language', i18n.language_choice()]
                code = self.run(args, ask=self.channel.ask, secret=self.channel.secret, write=self.channel.console)
            except Exception:
                # Startup/storage errors outside cli.main's handler must stay visible,
                # without exposing exception text that could contain credentials.
                self.events.event.emit('error-heading', 'Could not start this operation')
                self.events.event.emit('error', 'Check that your user account can write to its application data folder. You can report this problem using Open an issue below.')
                code = 1
            self.events.event.emit('done', code)
        self.worker = threading.Thread(target=work, name='cytv-install', daemon=False)
        self.worker.start()

    def receive(self, kind, value):
        if kind == 'step':
            number, title, clear = value
            if self.command == 'install':
                self.title.setText(tr(title))
                self.subtitle.hide()
                self.badge.setText(tr(f'Step {number} of 4'))
                self.update_steps(number)
            else:
                self.title.setText(tr(self.operation_title))
                self.subtitle.setText(tr(title))
                self.subtitle.show()
                self.badge.setText(tr('Maintenance action'))
            if clear:
                self.content.clear()
        elif kind in ('text', 'heading', 'error', 'error-heading'):
            text = tr(value)
            if kind == 'text' and text.endswith('.json') and 'diagnostic-' in text:
                path = Path(text.strip())
                if path.is_file():
                    self.report = path
            tag = 'h3' if kind in ('heading', 'error-heading') else 'p'
            color = '#ff6b6b' if kind.startswith('error') else '#f3ede3' if kind == 'heading' else '#c0b5a5'
            style = f' style="color: {color}"'
            self.content.append(f'<{tag}{style}>' + html.escape(text).replace('\n', '<br>') + f'</{tag}>')
        elif kind == 'prompt':
            self.show_prompt(value)
        elif kind == 'done':
            self.running = False
            self.set_error_state(value not in (0, 130))
            self.language.setEnabled(True)
            self.pending = None
            self.progress.hide()
            self.cancel.setText(tr('Close'))
            self.cancel.setEnabled(True)
            self.clear_form()
            self.title.setText(tr('Finished' if value == 0 else 'Cancelled' if value == 130 else 'Let’s resolve this'))
            self.subtitle.show()
            self.subtitle.setText(tr('Read the result below before continuing.'))
            self.rail_note.setText(tr('Read the result below before continuing.'))
            self.badge.setText(self.title.text())
            if self.command == 'install':
                self.update_steps(self.current_step, value)
            self.content.moveCursor(self.content.textCursor().MoveOperation.End)
            if self.report:
                self.button('Save diagnostic report…', self.save_report)
            if value not in (0, 130):
                self.button('Open an issue', lambda: QDesktopServices.openUrl(QUrl(diagnostics.ISSUE_URL)))
            self.button('Back to start', self.home, True)

    def show_prompt(self, prompt):
        self.pending = prompt
        self.progress.hide()
        self.cancel.setEnabled(True)
        self.clear_form()
        label = QLabel(tr('Connection check' if self.command != 'install' and prompt.label.startswith('Edition [') else prompt.title))
        label.setWordWrap(True)
        label.setObjectName('promptTitle')
        self.form_layout.addWidget(label)
        if prompt.kind == 'confirm':
            yes = self.button('Connect and remember' if prompt.label.startswith('Connect') else 'Continue', lambda: self.submit('y'), prompt.default == 'y')
            no = self.button('No, go back / cancel this operation', lambda: self.submit('n'), prompt.default == 'n')
            (yes if prompt.default == 'y' else no).setFocus()
            if prompt.label.startswith('Connect'):
                self.button('Connection details', lambda: self.submit('?'))
        elif prompt.kind == 'choice' and prompt.label.startswith('Edition'):
            options = QWidget()
            row = QHBoxLayout(options)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(12)
            group = QButtonGroup(options)
            for key, name, detail in prompt.options:
                card = EditionOption(tr(name), tr(detail), key)
                group.addButton(card)
                row.addWidget(card, 1)
                if key == prompt.default:
                    card.setChecked(True)
            self.form_layout.addWidget(options)
            proceed = self.button('Continue', lambda: self.submit(group.checkedButton().key), True)
            proceed.setEnabled(group.checkedButton() is not None)
            group.buttonToggled.connect(lambda: proceed.setEnabled(group.checkedButton() is not None))
            if group.checkedButton():
                group.checkedButton().setFocus()
        elif prompt.kind == 'choice':
            choices = Select()
            choices.setAccessibleName(tr(prompt.title))
            for key, name, detail in prompt.options:
                choices.addItem(tr(name) + (' — ' + tr(detail) if detail else ''), key)
                if key == prompt.default:
                    choices.setCurrentIndex(choices.count() - 1)
            self.form_layout.addWidget(choices)
            self.button('Continue', lambda: self.submit(choices.currentData()), True)
            choices.setFocus()
            if prompt.label.startswith('TV number'):
                # Saved-TV menus also use this label; retry is offered only for discovery.
                if any(name == 'Enter an IP address manually' for _, name, _ in prompt.options):
                    self.button('Search again', lambda: self.submit('r'))
        elif prompt.kind == 'ready':
            self.button('TV is on — check again', lambda: self.submit(''), True).setFocus()
        else:
            entry = QLineEdit()
            entry.setAccessibleName(tr(prompt.title))
            label.setBuddy(entry)
            if prompt.secret:
                entry.setEchoMode(QLineEdit.EchoMode.Password)
            elif 'IP address' in prompt.label:
                entry.setPlaceholderText(tr('For example, 192.168.1.50'))
            self.form_layout.addWidget(entry)
            def submit_entry():
                value = entry.text()
                entry.clear()
                self.submit(value)
            entry.returnPressed.connect(submit_entry)
            self.button('Continue', submit_entry, True)
            if prompt.kind == 'file':
                def choose_file():
                    filename, _ = QFileDialog.getOpenFileName(self, tr('Choose your existing SSH private key'))
                    if filename:
                        entry.setText(filename)
                self.button('Choose key file…', choose_file)
            if 'IP address' in prompt.label:
                self.button('Search again', lambda: self.submit('r'))
                self.button('Help finding my TV', lambda: self.submit('?'))
            entry.setFocus()

    def submit(self, value):
        if not self.pending:
            return
        self.pending = None
        self.clear_form()
        self.cancel.setEnabled(False)
        self.progress.show()
        self.channel.answer(value)

    def save_report(self):
        filename, _ = QFileDialog.getSaveFileName(self, tr('Save diagnostic report'), self.report.name, 'JSON (*.json)')
        if filename:
            try:
                if Path(filename).resolve() != self.report.resolve():
                    shutil.copyfile(self.report, filename)
            except OSError:
                self.error_dialog('Could not save report', 'Choose another folder and try again.')

    def closeEvent(self, event):
        if self.running:
            event.ignore()
            if self.pending:
                self.submit(None)
            else:
                QMessageBox.information(self, tr('Operation in progress'), tr('Please wait for this step to finish. This keeps installation and recovery data consistent.'))
        else:
            event.accept()


def main():
    app = QApplication(sys.argv[:1])
    for font in (cli.payload_dir() / 'fonts').glob('*.ttf'):
        QFontDatabase.addApplicationFont(str(font))
    QFont.insertSubstitutions(app.font().family(), ['Noto Sans', 'Noto Sans Devanagari', 'Noto Sans KR'])
    app.setApplicationName('Clean Your TV')
    app.setOrganizationName('CleanYourTV')
    app.setWindowIcon(QIcon(str(cli.payload_dir() / 'installer.png')))
    app.setStyle('Fusion')
    window = Wizard()
    window.show()
    if '--smoke-test' in sys.argv:
        QTimer.singleShot(200, app.quit)
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
