import subprocess
from typing import Dict, List, NamedTuple

from albert import Action, Item, Query, QueryHandler, runDetachedProcess  # pylint: disable=import-error


md_iid = '0.5'
md_version = '1.0'
md_name = 'Window Switcher Steven'
md_description = 'List and manage X11 windows.'
md_url = 'https://github.com/stevenxxiu/albert_window_switcher_steven'
md_maintainers = '@stevenxxiu'
md_bin_dependencies = ['wmctrl']


class Window(NamedTuple):
    wid: str
    desktop: str
    wm_class: str
    host: str
    wm_name: str


def parse_window(line: str) -> Window:
    win_id, desktop, rest = line.split(None, 2)
    win_class, rest = rest.split('  ', 1)
    host, title = rest.strip().split(None, 1)

    return Window(win_id, desktop, win_class, host, title)


def find_win_instance_class(wm_class: str) -> (str, str):
    match wm_class:
        case 'org.wezfurlong.wezterm.org.wezfurlong.wezterm':
            return 'org.wezfurlong.wezterm', 'WezTerm'
        case 'texmacs.bin.texmacs.bin':
            return 'texmacs.bin', 'TeXmacs'
        case _:
            parts = wm_class.replace(' ', '-').split('.')
            return parts if len(parts) == 2 else ('', '')


WM_CLASS_TO_ICON_NAME: Dict[str, str] = {
    'jetbrains-clion.jetbrains-clion': 'xdg:clion',
    'jetbrains-idea.jetbrains-idea': 'xdg:intellij-idea-ultimate-edition',
    'jetbrains-pycharm.jetbrains-pycharm': 'xdg:pycharm',
    'PDF Studio Pro.PDF Studio Pro': 'xdg:pdfstudio',
    'subl.Subl': 'xdg:sublime-text',
    'texmacs.bin.texmacs.bin': 'xdg:TeXmacs',
    'vivaldi-stable.Vivaldi-stable': 'xdg:vivaldi',
}


def get_icons(wm_class: str, win_instance: str, win_class: str) -> List[str]:
    res = []
    if wm_class in WM_CLASS_TO_ICON_NAME:
        res = [WM_CLASS_TO_ICON_NAME[wm_class]]
    return [*res, f'xdg:{win_instance}', f'xdg:{win_class.lower()}']


class Plugin(QueryHandler):
    def id(self) -> str:
        return __name__

    def name(self) -> str:
        return md_name

    def description(self) -> str:
        return md_description

    def synopsis(self) -> str:
        return 'filter'

    def handleQuery(self, query: Query) -> None:
        stripped = query.string.strip().lower()
        if not stripped:
            return
        for line in subprocess.check_output(['wmctrl', '-l', '-x'], text=True).splitlines():
            win = Window(*parse_window(line))

            if win.desktop == '-1':
                continue

            (win_instance, win_class) = find_win_instance_class(win.wm_class)  # pylint: disable=unpacking-non-sequence
            matches = [win_instance.lower(), win_class.lower(), win.wm_name.lower()]

            if any(stripped in match for match in matches):
                item = Item(
                    id=f'{md_name}/{win.wid}',
                    text=f'{win_class.replace("-", " ")} - <i>Desktop {win.desktop}</i>',
                    subtext=win.wm_name,
                    icon=get_icons(win.wm_class, win_instance, win_class.lower()),
                    actions=[
                        Action(
                            f'{md_name}/switch/{win.wid}',
                            'Switch Window',
                            lambda wid=win.wid: runDetachedProcess(['wmctrl', '-i', '-a', wid]),
                        ),
                        Action(
                            f'{md_name}/move_to_desktop/{win.wid}',
                            'Move window to this desktop',
                            lambda wid=win.wid: runDetachedProcess(['wmctrl', '-i', '-R', wid]),
                        ),
                        Action(
                            f'{md_name}/close/{win.wid}',
                            'Close the window gracefully',
                            lambda wid=win.wid: runDetachedProcess(['wmctrl', '-i', '-c', wid]),
                        ),
                    ],
                )
                query.add(item)
