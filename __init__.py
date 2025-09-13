import asyncio
import enum
import sys
import time
from enum import Enum
from pathlib import Path
from threading import Thread
from typing import Callable, Self, cast, override

sys.path.insert(1, str(next(Path(__file__).parent.glob('__pypackages__/*/lib'))))
from albert import (
    Action,
    Item,
    Matcher,
    PluginInstance,
    Query,
    StandardItem,
    TriggerQueryHandler,
)
from i3ipc.aio import Connection  # pyright: ignore[reportPrivateLocalImportUsage]
from i3ipc.aio import connection
from i3ipc.replies import CommandReply

md_iid = '3.0'
md_version = '1.5'
md_name = 'Window Switcher Steven'
md_description = 'List and manage Sway windows'
md_license = 'MIT'
md_url = 'https://github.com/stevenxxiu/albert_window_switcher_steven'
md_authors = ['@stevenxxiu']

APP_ID_TO_ICON_NAME: dict[str, str] = {
    'texmacs': 'xdg:TeXmacs',
}


def get_icon_urls(app_id: str) -> list[str]:
    res = []
    if app_id in APP_ID_TO_ICON_NAME:
        res = [APP_ID_TO_ICON_NAME[app_id]]
    return [*res, f'xdg:{app_id}']


class SwayTreeNode(connection.Con):
    id: int  # pyright: ignore[reportUninitializedInstanceVariable]
    type: str
    name: str  # pyright: ignore[reportUninitializedInstanceVariable]
    pid: int | None  # pyright: ignore[reportUninitializedInstanceVariable]
    app_id: str | None  # pyright: ignore[reportUninitializedInstanceVariable]

    @override
    def workspace(self) -> Self:
        return self

    @override
    async def command(self, command: str) -> list[CommandReply]:
        return []


async def focus_window(node: SwayTreeNode) -> None:
    _ = await node.command('focus')


async def kill_window(node: SwayTreeNode) -> None:
    _ = await node.command('kill')


def get_tab_index(node: SwayTreeNode) -> int | None:
    if not node.parent:
        return None
    parent = cast(SwayTreeNode, node.parent)
    if not parent.parent:
        return None
    siblings: list[SwayTreeNode] = parent.nodes  # pyright: ignore[reportUnknownMemberType]
    for i, cur_node in enumerate(siblings):
        if cur_node.id == node.id:
            return i


class MoveMode(Enum):
    MOVE_SELECTED_TO_FOCUSED = enum.auto()
    MOVE_FOCUSED_TO_SELECTED = enum.auto()


async def move_window(sway: Connection, node: SwayTreeNode, move_mode: MoveMode) -> None:
    time.sleep(0.1)  # Wait until *Albert Launcher* closes

    tree = await sway.get_tree()
    focused = tree.find_focused()
    if not focused:
        return
    focused = cast(SwayTreeNode, focused)
    focused_i = get_tab_index(focused)
    tab_i = get_tab_index(node)

    if move_mode == MoveMode.MOVE_SELECTED_TO_FOCUSED:
        _ = await sway.command('mark --add move_dest')
        _ = await node.command('focus')
        _ = await node.command('move mark move_dest')
        # Running this once just moves the mark to the other window
        _ = await sway.command('mark --toggle move_dest')
        _ = await sway.command('mark --toggle move_dest')
    else:
        _ = await node.command('mark --add move_dest')
        _ = await sway.command('move mark move_dest')
        _ = await node.command('mark --toggle move_dest')

    if focused_i is not None and tab_i is not None:
        # When moving a top level window left, the new window becomes the right sibling by default. Always replace the
        # position.
        if move_mode == MoveMode.MOVE_SELECTED_TO_FOCUSED and focused_i < tab_i:
            _ = await sway.command('move left')
        if move_mode == MoveMode.MOVE_FOCUSED_TO_SELECTED and tab_i < focused_i:
            _ = await sway.command('move left')


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self) -> None:
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

    @override
    def synopsis(self, _query: str) -> str:
        return 'filter'

    @override
    def defaultTrigger(self) -> str:
        return 'w '

    async def asyncHandleTriggerQuery(self, query: Query) -> None:
        sway = await Connection().connect()
        matcher = Matcher(query.string)

        items: list[Item] = []
        tree = await sway.get_tree()
        for node in tree.descendants():
            node = cast(SwayTreeNode, node)
            if node.pid is None:
                continue
            if not (matcher.match(node.name) or (node.app_id is not None and matcher.match(node.app_id))):
                continue
            workspace_name = node.workspace().name
            floating_text: str = ' (floating)' if node.type == 'floating_con' else ''
            focus_call: Callable[[SwayTreeNode], None] = lambda node_=node: asyncio.run(focus_window(node_))  # noqa: E731
            kill_call: Callable[[SwayTreeNode], None] = lambda node_=node: asyncio.run(kill_window(node_))  # noqa: E731
            move_to_call: Callable[[SwayTreeNode], None] = lambda node_=node: Thread(  # noqa: E731
                target=asyncio.run, args=(move_window(sway, node_, MoveMode.MOVE_FOCUSED_TO_SELECTED),)
            ).start()
            move_from_call: Callable[[SwayTreeNode], None] = lambda node_=node: Thread(  # noqa: E731
                target=asyncio.run, args=(move_window(sway, node_, MoveMode.MOVE_SELECTED_TO_FOCUSED),)
            ).start()
            icon_urls = []
            if node.app_id is not None:
                icon_urls = get_icon_urls(node.app_id)
            item = StandardItem(
                id=self.id(),
                text=f'{node.name}{floating_text} - <i>Workspace {workspace_name}</i>',
                subtext=node.app_id or '',
                iconUrls=icon_urls,
                actions=[
                    Action(self.id(), 'Focus', focus_call),
                    Action(self.id(), 'Kill', kill_call),
                    Action(self.id(), 'Move to', move_to_call),
                    Action(self.id(), 'Move from', move_from_call),
                ],
            )
            items.append(item)
        query.add(items)  # pyright: ignore[reportUnknownMemberType]

    @override
    def handleTriggerQuery(self, query: Query) -> None:
        asyncio.run(self.asyncHandleTriggerQuery(query))
