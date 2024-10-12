from typing import Callable, ParamSpec

from albert import Action, Matcher, PluginInstance, StandardItem, TriggerQueryHandler  # pylint: disable=import-error
from ewmh import EWMH


md_iid = '2.3'
md_version = '1.3'
md_name = 'Window Switcher Steven'
md_description = 'List and manage X11 windows'
md_url = 'https://github.com/stevenxxiu/albert_window_switcher_steven'
md_maintainers = '@stevenxxiu'
md_lib_dependencies = ['ewmh']


WM_CLASS_TO_ICON_NAME: dict[tuple[str, str], str] = {
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
    def __init__(self):
        TriggerQueryHandler.__init__(
            self, id=__name__, name=md_name, description=md_description, synopsis='filter', defaultTrigger='w '
        )
        PluginInstance.__init__(self)
        self.ewmh = EWMH()

    def with_flush(self, func: Callable[..., None]) -> Callable[..., None]:
        def wrapper(*args, **kwargs) -> None:
            func(*args, **kwargs)
            self.ewmh.display.flush()

        return wrapper

    def handleTriggerQuery(self, query) -> None:
        matcher = Matcher(query.string)

        cur_desktop = self.ewmh.getCurrentDesktop()
        windows = self.ewmh.getClientList()
        for window in windows:
            assert window is not None

            if self.ewmh.getWmDesktop(window) == 0xFFFFFFFF:
                continue

            wm_class = window.get_wm_class()
            assert wm_class is not None
            (win_instance, win_class) = wm_class

            win_desktop = self.ewmh.getWmDesktop(window)

            wm_name = self.ewmh.getWmName(window)
            assert wm_name is not None
            win_wm_name = wm_name.decode()

            if matcher.match(win_instance) or matcher.match(win_class) or matcher.match(win_wm_name):
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
