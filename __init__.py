# -*- coding: utf-8 -*-

'''List and manage X11 windows.

Synopsis: <filter>'''

import subprocess
from collections import namedtuple

from albert import Item, ProcAction, iconLookup  # pylint: disable=import-error


__title__ = 'Window Switcher'
__version__ = '0.4.5'
__authors__ = ['Ed Perez', 'manuelschneid3r', 'dshoreman']
__exec_deps__ = ['wmctrl']

Window = namedtuple('Window', ['wid', 'desktop', 'wm_class', 'host', 'wm_name'])


def parse_window(line):
    win_id, desktop, rest = line.decode().split(None, 2)
    win_class, rest = rest.split('  ', 1)
    host, title = rest.strip().split(None, 1)

    return [win_id, desktop, win_class, host, title]


def handleQuery(query):
    stripped = query.string.strip().lower()
    if not stripped:
        return None
    results = []
    for line in subprocess.check_output(['wmctrl', '-l', '-x']).splitlines():
        win = Window(*parse_window(line))

        if win.desktop == '-1':
            continue

        match win.wm_class:
            case 'org.wezfurlong.wezterm.org.wezfurlong.wezterm':
                win_instance, win_class = 'org.wezfurlong.wezterm', 'org.wezfurlong.wezterm'
            case _:
                parts = win.wm_class.replace(' ', '-').split('.')
                (win_instance, win_class) = parts if len(parts) == 2 else ('', '')
        matches = [win_instance.lower(), win_class.lower(), win.wm_name.lower()]

        if any(stripped in match for match in matches):
            match win.wm_class:
                case 'subl.Subl':
                    icon_path = iconLookup('sublime-text')
                case 'vivaldi-stable.Vivaldi-stable':
                    icon_path = iconLookup('vivaldi')
                case _:
                    icon_path = iconLookup(win_instance) or iconLookup(win_class.lower())
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
