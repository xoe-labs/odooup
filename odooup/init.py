#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from collections import OrderedDict

import click

from ._helpers import call_cmd, replace_in_file
from ._installers import install_tools
from .clone import clone_submodule_to_target, get_vendor_target

ODOO_VERSIONS = OrderedDict(
    [("10", "10.0"), ("11", "11.0"), ("12", "12.0"), ("m", "master")]
)

IS_GIT_URL_REGEXP = (
    r"(?:git|ssh|https?|git@[-\w.]+):(\/\/)?(.*?)(\.git)(\/?|\#[-\d\w._]+?)$"
)


class OdooVersionChoice(click.types.Choice):
    name = "odoo-version"

    def __init__(self, versions, case_sensitive=True):
        self.versions = versions
        super(OdooVersionChoice, self).__init__(self.versions.keys(), case_sensitive)

    def convert(self, value, param, ctx):
        value = super(OdooVersionChoice, self).convert(value, param, ctx)
        return self.versions[value]


class GitRepo(click.types.StringParamType):
    name = "git-repo"

    def convert(self, value, param, ctx):
        value = super(GitRepo, self).convert(value, param, ctx)
        found = re.match(IS_GIT_URL_REGEXP, value)

        if not found:
            self.fail(click.style(value, fg="red") + " is not a git url", param, ctx)

        return value


def ask_for_additional_repos():
    additional_repos = []
    fist_repo = True
    while True:
        msg = "Add additional repo" if fist_repo else "Add another repo"
        add_new = click.confirm(msg, default=False)
        if not add_new:
            break
        repo = click.prompt("Enter Repo", type=GitRepo())
        fist_repo = False
        additional_repos += [repo]
    return additional_repos


@click.command()
@click.option(
    "--odoo-version",
    type=OdooVersionChoice(ODOO_VERSIONS),
    prompt="Please select Odoo version: \n Available: "
    + ", ".join(["{}".format(v) for v in ODOO_VERSIONS.values()])
    + "\n Select:",
)
@click.option(
    "--is-enterprise",
    is_flag=True,
    default=False,
    prompt="Use Odoo Enterprise (access required)",
    help="Clone enterprise repository (access required).",
)
@click.argument("project", required=True)
def init(odoo_version, is_enterprise, project):
    """ Bootstrap you Odoo project """
    additional_repos = ask_for_additional_repos()
    project = project.lower()  # docker doesn't permit uppercase project names

    click.echo("")
    click.secho("Your choices: ", fg="black", bg="bright_green", bold=True)
    click.echo("")
    click.echo("Odoo Edition:      ", nl=False)
    ee = "EE (Enterprise Edition)"
    ce = "CE (Community Edition)"
    click.secho(
        "Odoo " + odoo_version + " " + (ee if is_enterprise else ce),
        fg="yellow",
        bold=True,
    )
    click.echo("")
    click.secho("Get some work done ...", fg="black", bg="bright_green", bold=True)
    click.echo("")

    install_tools()

    if (
        project
        and call_cmd("git rev-parse --is-inside-work-tree", exit_on_error=False)
        == "true"
    ):
        click.get_current_context().fail(
            "You are trying to launch a new project inside a git repository"
        )
    elif project:
        call_cmd(
            "git clone https://github.com/xoe-labs/dockery-odoo-scaffold.git {}".format(
                project
            )
        )
        current_directory = os.getcwd()
        final_directory = os.path.join(current_directory, project)
        click.echo("Switching to: " + click.style(final_directory, fg="yellow"))
        os.chdir(final_directory)
        call_cmd("git remote rename origin scaffold")
        call_cmd("git branch --unset-upstream")

    # Repo cloning
    for repo_url in additional_repos:
        clone_submodule_to_target(odoo_version, repo_url, get_vendor_target(repo_url))
    clone_submodule_to_target(
        odoo_version, "https://github.com/odoo/odoo.git", "./vendor/odoo/cc"
    )
    if is_enterprise:
        clone_submodule_to_target(
            odoo_version, "https://github.com/odoo/enterprise.git", "./vendor/odoo/ee"
        )

    # Seed Placeholders
    replacements = {
        ("Dockerfile", ".env"): [
            {"from": "{{ PROJECT }}", "to": project},
            {"from": "{{ DEFAULT_BRANCH }}", "to": odoo_version},
        ]
    }
    for files, rules in replacements.items():
        for rule in rules:
            replace_in_file(files, rule["from"], rule["to"])

    # Git commit
    call_cmd("git add .")
    call_cmd('git commit -m "Customize Project"')

    call_cmd("git config commit.template $(pwd)/.git-commit-template")
    call_cmd("pre-commit install --hook-type pre-commit")
    call_cmd("pre-commit install --hook-type commit-msg")
    call_cmd("pre-commit install --install-hooks")
    click.echo(
        "Next, run: " + click.style("`cd {} && make info`".format(project), fg="yellow")
    )


if __name__ == "__main__":
    init()
