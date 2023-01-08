# User Customized Window Switcher Extension
## Install
To install, copy or symlink this directory to `~/.local/share/albert/org.albert.extension.python/modules/window_switcher_user/`.

## Development Setup
To setup the project for development, run:

    $ cd window_switcher_user/
    $ pre-commit install --hook-type pre-commit --hook-type commit-msg

To lint and format files, run:

    $ pre-commit run --all-files
