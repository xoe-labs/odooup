# Copyright 2019 XOE Labs (<https://xoe.solutions>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from click.testing import CliRunner

from odooup import main


def tests_init_run():
    result = CliRunner().invoke(main, ["init", "--odoo-version=12", "project-name"])
    # We are launching inside a git repository
    assert result.exit_code != 0
