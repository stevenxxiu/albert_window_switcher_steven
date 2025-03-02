# Albert Launcher Window Switcher Extension
List and manage *X11* windows.

## Install
To install, copy or symlink this directory to `~/.local/share/albert/python/plugins/window_switcher_steven/`.

## Development Setup
To setup the project for development, run:

    $ cd window_switcher_steven/
    $ pre-commit install --hook-type pre-commit --hook-type commit-msg
    $ mkdir stubs/
    $ ln --symbolic ~/.local/share/albert/python/plugins/albert.pyi stubs/

To lint and format files, run:

    $ pre-commit run --all-files
