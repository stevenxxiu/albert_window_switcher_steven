'''List and manage X11 windows.

Synopsis: <filter>'''

import subprocess
from collections import namedtuple

from albert import Item, ProcAction, iconLookup  # pylint: disable=import-error


__title__ = 'Window Switcher User'
__version__ = '0.4.6'
__authors__ = ['Steven Xu', 'Ed Perez', 'manuelschneid3r', 'dshoreman']
__exec_deps__ = ['wmctrl']

Window = namedtuple('Window', ['wid', 'desktop', 'wm_class', 'host', 'wm_name'])


def parse_window(line):
    win_id, desktop, rest = line.split(None, 2)
    win_class, rest = rest.split('  ', 1)
    host, title = rest.strip().split(None, 1)

    return [win_id, desktop, win_class, host, title]


def find_win_instance_class(wm_class):
    match wm_class:
        case 'org.wezfurlong.wezterm.org.wezfurlong.wezterm':
            return 'org.wezfurlong.wezterm', 'WezTerm'
        case 'texmacs.bin.texmacs.bin':
            return 'texmacs.bin', 'TeXmacs'
        case _:
            parts = wm_class.replace(' ', '-').split('.')
            return parts if len(parts) == 2 else ('', '')


def find_icon_path(wm_class, win_instance, win_class):
    try:
        wm_class_to_icon_name = {
            'jetbrains-clion.jetbrains-clion': 'clion',
            'jetbrains-idea.jetbrains-idea': 'intellij-idea-ultimate-edition',
            'jetbrains-pycharm.jetbrains-pycharm': 'pycharm',
            'PDF Studio Pro.PDF Studio Pro': 'pdfstudio',
            'subl.Subl': 'sublime-text',
            'texmacs.bin.texmacs.bin': 'TeXmacs',
            'vivaldi-stable.Vivaldi-stable': 'vivaldi',
        }
        return iconLookup(wm_class_to_icon_name[wm_class])
    except KeyError:
        return iconLookup(win_instance) or iconLookup(win_class.lower())


def handleQuery(query):
    stripped = query.string.strip().lower()
    if not stripped:
        return None
    results = []
    for line in subprocess.check_output(['wmctrl', '-l', '-x'], text=True).splitlines():
        win = Window(*parse_window(line))

        if win.desktop == '-1':
            continue

        (win_instance, win_class) = find_win_instance_class(win.wm_class)  # pylint: disable=unpacking-non-sequence
        matches = [win_instance.lower(), win_class.lower(), win.wm_name.lower()]

        if any(stripped in match for match in matches):
            icon_path = find_icon_path(win.wm_class, win_instance, win_class)
            results.append(
                Item(
                    id=f'{__title__}{win.wm_class}',
                    icon=icon_path,
                    text=f'{win_class.replace("-", " ")}  - <i>Desktop {win.desktop}</i>',
                    subtext=win.wm_name,
                    actions=[
                        ProcAction('Switch Window', ['wmctrl', '-i', '-a', win.wid]),
                        ProcAction('Move window to this desktop', ['wmctrl', '-i', '-R', win.wid]),
                        ProcAction('Close the window gracefully.', ['wmctrl', '-c', win.wid]),
                    ],
                )
            )
    return results
