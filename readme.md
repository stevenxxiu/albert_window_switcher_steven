# Albert Launcher Window Switcher Extension
List and manage *X11* windows.

## Install
To install, copy or symlink this directory to `~/.local/share/albert/python/plugins/window_switcher_steven/`.

## Development Setup
To setup the project for development, run:

    $ cd window_switcher_steven/
    $ pre-commit install --hook-type pre-commit --hook-type commit-msg
    $ mkdir --parents typings/albert/
    $ ln --symbolic ~/.local/share/albert/python/plugins/albert.pyi typings/albert/__init__.pyi

To lint and format files, run:

    $ pre-commit run --all-files
