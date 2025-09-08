import asyncio
from typing import Callable, Self, cast, override

from albert import (
    Action,
    Matcher,
    PluginInstance,
    Query,
    StandardItem,
    TriggerQueryHandler,
)
from i3ipc.aio import Connection  # pyright: ignore[reportPrivateLocalImportUsage]
from i3ipc.aio import connection

md_iid = '3.0'
md_version = '1.5'
md_name = 'Window Switcher Steven'
md_description = 'List and manage Sway windows'
md_license = 'MIT'
md_url = 'https://github.com/stevenxxiu/albert_window_switcher_steven'
md_authors = ['@stevenxxiu']
md_lib_dependencies = ['i3ipc']


APP_ID_TO_ICON_NAME: dict[str, str] = {
    'texmacs': 'xdg:TeXmacs',
}


def get_icon_urls(app_id: str) -> list[str]:
    res = []
    if app_id in APP_ID_TO_ICON_NAME:
        res = [APP_ID_TO_ICON_NAME[app_id]]
    return [*res, f'xdg:{app_id}']


class SwayTreeNode(connection.Con):
    type: str
    name: str  # pyright: ignore[reportUninitializedInstanceVariable]
    pid: int | None  # pyright: ignore[reportUninitializedInstanceVariable]
    app_id: str | None  # pyright: ignore[reportUninitializedInstanceVariable]

    @override
    def workspace(self) -> Self:
        return self

    @override
    def command(self, cmd: str) -> None:
        pass


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

        items = []
        tree = await sway.get_tree()
        for node in tree.descendants():
            node = cast(SwayTreeNode, node)
            if node.pid is None:
                continue
            if not (matcher.match(node.name) or (node.app_id is not None and matcher.match(node.app_id))):
                continue
            workspace_name = node.workspace().name
            floating_text: str = ' (floating)' if node.type == 'floating_con' else ''
            switch_window_call: Callable[[SwayTreeNode], None] = lambda node_=node: asyncio.run(node_.command('focus'))  # noqa: E731  # pyright: ignore[reportUnknownLambdaType, reportArgumentType]
            icon_urls = []
            if node.app_id is not None:
                icon_urls = get_icon_urls(node.app_id)
            items.append(  # pyright: ignore[reportUnknownMemberType]
                StandardItem(
                    id=self.id(),
                    text=f'{node.name}{floating_text} - <i>Workspace {workspace_name}</i>',
                    subtext=node.app_id or '',
                    iconUrls=icon_urls,
                    actions=[
                        Action(
                            self.id(),
                            'Switch Window',
                            switch_window_call,
                        ),
                    ],
                )
            )
        query.add(items)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    @override
    def handleTriggerQuery(self, query: Query) -> None:
        asyncio.run(self.asyncHandleTriggerQuery(query))
