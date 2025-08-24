import inspect
import json
import subprocess
from dataclasses import dataclass
from typing import Any, Callable, ParamSpec, override

from albert import (
    Action,
    Matcher,
    PluginInstance,
    Query,
    StandardItem,
    TriggerQueryHandler,
)

md_iid = '3.0'
md_version = '1.5'
md_name = 'Window Switcher Steven'
md_description = 'List and manage X11 windows'
md_license = 'MIT'
md_url = 'https://github.com/stevenxxiu/albert_window_switcher_steven'
md_authors = ['@stevenxxiu']


APP_ID_TO_ICON_NAME: dict[str, str] = {
    'texmacs': 'xdg:TeXmacs',
}


def get_icon_urls(app_id: str) -> list[str]:
    print(app_id)
    res = []
    if app_id in APP_ID_TO_ICON_NAME:
        res = [APP_ID_TO_ICON_NAME[app_id]]
    return [*res, f'xdg:{app_id}']


def switch_window(id: int) -> None:
    _ = subprocess.call(['swaymsg', f'[con_id={id}]', 'focus'])


Param = ParamSpec('Param')


@dataclass
class SwayTreeNode:
    id: int
    type: str
    name: str
    floating_nodes: list['SwayTreeNode']
    nodes: list['SwayTreeNode']
    pid: int | None
    app_id: str | None

    @classmethod
    def from_dict(cls, env: dict[str, Any]):  # pyright: ignore[reportExplicitAny]
        _ = env.setdefault('pid', None)
        _ = env.setdefault('app_id', None)
        if 'floating_nodes' in env:
            env['floating_nodes'] = [SwayTreeNode.from_dict(node) for node in env['floating_nodes']]  # pyright: ignore[reportAny]
        if 'nodes' in env:
            env['nodes'] = [SwayTreeNode.from_dict(node) for node in env['nodes']]  # pyright: ignore[reportAny]
        return cls(
            **{  # pyright: ignore[reportAny]
                k: v
                for k, v in env.items()  # pyright: ignore[reportAny]
                if k in inspect.signature(cls).parameters
            }
        )


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

    @override
    def synopsis(self, _query: str) -> str:
        return 'filter'

    @override
    def defaultTrigger(self):
        return 'w '

    @override
    def handleTriggerQuery(self, query: Query) -> None:
        matcher = Matcher(query.string)

        root_node = SwayTreeNode.from_dict(
            json.loads(subprocess.check_output(['swaymsg', '--type', 'get_tree', '--raw']))  # pyright: ignore[reportAny]
        )
        stack: list[tuple[str | None, SwayTreeNode]] = [(None, root_node)]
        items: list[StandardItem] = []
        while stack:
            workspace, cur_node = stack.pop()
            if cur_node.type == 'workspace':
                workspace = cur_node.name
            if cur_node.pid is not None:
                assert cur_node.app_id is not None
                if matcher.match(cur_node.app_id) or matcher.match(cur_node.name):
                    floating_text = ' (floating)' if cur_node.type == 'floating_con' else ''
                    switch_window_call: Callable[[int], None] = lambda id_=cur_node.id: switch_window(id_)  # noqa: E731
                    item = StandardItem(
                        id=f'{md_name}/{cur_node.id}',
                        text=f'{cur_node.app_id}{floating_text} - <i>Workspace {workspace}</i>',
                        subtext=cur_node.name,
                        iconUrls=get_icon_urls(cur_node.app_id),
                        actions=[
                            Action(
                                f'{md_name}/switch/{cur_node.id}',
                                'Switch Window',
                                switch_window_call,
                            ),
                        ],
                    )
                    items.append(item)

            stack.extend([(workspace, child) for child in cur_node.nodes])
            stack.extend([(workspace, child) for child in cur_node.floating_nodes])

        for item in items:
            query.add(item)  # pyright: ignore[reportUnknownMemberType]
