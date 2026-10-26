#!/usr/bin/env python3
"""Capture the real Qt widgets with offline sample events. Never contacts a TV.

Requires the desktop dependencies. Run from any directory:
    python scripts/preview-installer.py --language ru
Output goes to build/installer-preview, or --output PATH.
"""
import argparse
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont
from cytv import i18n
from cytv.gui import Wizard
from cytv.desktop import Prompt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=i18n.LANGUAGES, default='ru')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/installer-preview')
    parser.add_argument('--all-locales', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    app.setStyle('Fusion')
    for font in (ROOT / 'launcher/fonts').glob('Noto*.ttf'):
        QFontDatabase.addApplicationFont(str(font))
    QFont.insertSubstitutions(app.font().family(), ['Noto Sans', 'Noto Sans Devanagari', 'Noto Sans KR'])
    with tempfile.TemporaryDirectory() as directory, \
            patch('cytv.state.default_dir', return_value=Path(directory)), \
            patch('cytv.i18n.system_languages', return_value=[args.language]):
        window = Wizard()
        window.language.setCurrentIndex(list(i18n.LANGUAGES).index(args.language))
        window.show()

        def capture(name):
            app.processEvents()
            target = args.output / (name + '-' + args.language + '.png')
            if not window.grab().save(str(target)):
                raise RuntimeError('Could not save preview: ' + str(target))

        capture('01-start')
        window.maintenance_toggle.click()
        capture('02-maintenance')
        window.home()
        window.preview.hide()
        window.receive('step', (1, 'Connect to your TV', True))
        window.receive('text', 'cytv will look for your TV automatically. Keep the remote nearby to approve pairing on the TV.')
        window.show_prompt(Prompt('TV IP address: '))
        capture('03-connect')
        window.receive('step', (2, 'Choose your edition', True))
        window.receive('text', 'TV: 192.168.1.50')
        window.receive('heading', 'Connection check')
        window.receive('text', 'Developer Mode SSH detected.')
        window.receive('text', 'No-root and Root are equal options for different TV setups.')
        window.show_prompt(Prompt('Edition [1]: ', [
            ('1', 'No-root', 'For a TV without root. Uses LG Developer Mode.'),
            ('2', 'Root', 'For an already rooted TV with existing SSH access.')]))
        capture('04-edition')
        window.receive('step', (4, 'Review and install', True))
        window.receive('heading', 'Root is ready')
        window.receive('text', 'Home control is on and Clean Your TV Home was opened.')
        window.receive('text', 'Home control stays on until you turn it off. The computer can now be switched off.')
        window.receive('done', 0)
        capture('05-finished')
        if args.all_locales:
            for code in i18n.LANGUAGES:
                window.language.setCurrentIndex(list(i18n.LANGUAGES).index(code))
                window.resize(900, 680)
                app.processEvents()
                if not window.grab().save(str(args.output / ('locale-' + code + '.png'))):
                    raise RuntimeError('Could not save locale preview: ' + code)
        window.close()
    print('Offline installer screenshots:', args.output)


if __name__ == '__main__':
    main()
