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


def find_win_instance_class(wm_class):
    match wm_class:
        case 'org.wezfurlong.wezterm.org.wezfurlong.wezterm':
            return 'org.wezfurlong.wezterm', 'org.wezfurlong.wezterm'
        case _:
            parts = wm_class.replace(' ', '-').split('.')
            return parts if len(parts) == 2 else ('', '')


def find_icon_path(wm_class, win_instance, win_class):
    match wm_class:
        case 'subl.Subl':
            return iconLookup('sublime-text')
        case 'vivaldi-stable.Vivaldi-stable':
            return iconLookup('vivaldi')
        case _:
            return iconLookup(win_instance) or iconLookup(win_class.lower())


def handleQuery(query):
    stripped = query.string.strip().lower()
    if not stripped:
        return None
    results = []
    for line in subprocess.check_output(['wmctrl', '-l', '-x']).splitlines():
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
