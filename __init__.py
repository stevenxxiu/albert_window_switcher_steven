from typing import Callable, ParamSpec

from albert import (  # pylint: disable=import-error
    Action,
    PluginInstance,
    StandardItem,
    TriggerQuery,
    TriggerQueryHandler,
)
from ewmh import EWMH


md_iid = '2.0'
md_version = '1.2'
md_name = 'Window Switcher Steven'
md_description = 'List and manage X11 windows'
md_url = 'https://github.com/stevenxxiu/albert_window_switcher_steven'
md_maintainers = '@stevenxxiu'
md_lib_dependencies = ['ewmh']


WM_CLASS_TO_ICON_NAME: dict[(str, str), str] = {
    ('gimp-2.10', 'Gimp-2.10'): 'xdg:gimp',
    ('jetbrains-clion', 'jetbrains-clion'): 'xdg:clion',
    ('jetbrains-idea', 'jetbrains-idea'): 'xdg:intellij-idea-ultimate-edition',
    ('jetbrains-pycharm', 'jetbrains-pycharm'): 'xdg:pycharm',
    ('nomacs', 'Image Lounge'): 'xdg:org.nomacs.ImageLounge',
    ('PDF Studio Pro', 'PDF Studio Pro'): 'xdg:pdfstudio',
    ('subl', 'Subl'): 'xdg:sublime-text',
    ('texmacs.bin', 'texmacs.bin'): 'xdg:TeXmacs',
    ('vencorddesktop', 'VencordDesktop'): 'xdg:vencord-desktop',
    ('vivaldi-stable', 'Vivaldi-stable'): 'xdg:vivaldi',
}


def get_icon_urls(win_instance: str, win_class: str) -> list[str]:
    res = []
    if (win_instance, win_class) in WM_CLASS_TO_ICON_NAME:
        res = [WM_CLASS_TO_ICON_NAME[(win_instance, win_class)]]
    return [*res, f'xdg:{win_instance}', f'xdg:{win_class.lower()}']


Param = ParamSpec('Param')


class Plugin(PluginInstance, TriggerQueryHandler):
    ewmh: EWMH | None = None

    def __init__(self):
        TriggerQueryHandler.__init__(
            self, id=__name__, name=md_name, description=md_description, synopsis='filter', defaultTrigger='w'
        )
        PluginInstance.__init__(self, extensions=[self])

    def initialize(self) -> None:
        self.ewmh = EWMH()

    def with_flush(self, func: Callable[Param, None]) -> Callable[Param, None]:
        def wrapper(*args, **kwargs) -> None:
            func(*args, **kwargs)
            self.ewmh.display.flush()

        return wrapper

    def handleTriggerQuery(self, query: TriggerQuery) -> None:
        stripped = query.string.strip().lower()
        cur_desktop = self.ewmh.getCurrentDesktop()
        windows = self.ewmh.getClientList()
        for window in windows:
            if self.ewmh.getWmDesktop(window) == 0xFFFFFFFF:
                continue

            (win_instance, win_class) = window.get_wm_class()
            win_desktop = self.ewmh.getWmDesktop(window)
            win_wm_name = self.ewmh.getWmName(window).decode()
            matches = [win_instance.lower(), win_class.lower(), win_wm_name.lower()]

            if any(stripped in match for match in matches):
                item = StandardItem(
                    id=f'{md_name}/{window.id}',
                    text=f'{win_class} - <i>Desktop {win_desktop}</i>',
                    subtext=win_wm_name,
                    iconUrls=get_icon_urls(win_instance, win_class),
                    actions=[
                        Action(
                            f'{md_name}/switch/{window.id}',
                            'Switch Window',
                            self.with_flush(lambda window_=window: self.ewmh.setActiveWindow(window_)),
                        ),
                        Action(
                            f'{md_name}/move_to_desktop/{window.id}',
                            'Move window to this desktop',
                            self.with_flush(lambda window_=window: self.ewmh.setWmDesktop(window_, cur_desktop)),
                        ),
                        Action(
                            f'{md_name}/close/{window.id}',
                            'Close the window gracefully',
                            self.with_flush(lambda window_=window: self.ewmh.setCloseWindow(window_)),
                        ),
                    ],
                )
                query.add(item)
