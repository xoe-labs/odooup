#!/usr/bin/env python
# Copyright 2019 XOE Labs (<https://xoe.solutions>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import click
from click_plugins import with_plugins
from pkg_resources import iter_entry_points

CONTEXT_SETTINGS = dict(auto_envvar_prefix="ODOOUP")


@with_plugins(iter_entry_points("core_package.cli_plugins"))
@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    """Commandline interface for odooup commands."""
    pass
