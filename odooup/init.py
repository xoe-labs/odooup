#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from collections import OrderedDict
from distutils.spawn import find_executable

import click

from ._helpers import call_cmd, mkdir_p, replace_in_file
from ._installers import install_compose_impersonation, install_make, install_precommit

ODOO_VERSIONS = OrderedDict(
    [("10", "10.0"), ("11", "11.0"), ("12", "12.0"), ("m", "master")]
)

IS_GIT_URL_REGEXP = (
    r"(?:git|ssh|https?|git@[-\w.]+):(\/\/)?(.*?)(\.git)(\/?|\#[-\d\w._]+?)$"
)
REPO_REGEXP = "(?P<host>(git@|https://)([\\w\\.@]{1,})(/|:))(?P<owner>[\\w,\\-,_]{1,})/(?P<repo>[\\w,\\-,_]{1,})(.git){0,1}((/){0,1})"  # noqa


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


def clone_target(odoo_version, url, target, shallow, reference_project):
    if not shallow:
        call_cmd(
            "git submodule add -b {odoo_version} {reference} "
            "{url} {target}".format(
                odoo_version=odoo_version,
                reference="--reference {}/{}".format(reference_project, target)
                if reference_project
                else "",
                url=url,
                target=target,
            ),
            echo_cmd=True,
            exit_on_error=False,
        )
    else:
        cmds = []
        cmds.append(
            "git config -f .git/config submodule.{target}.url {url}".format(
                target=target, url=url
            )
        )
        cmds.append(
            "git config -f .git/config submodule.{target}.active true".format(
                target=target
            )
        )
        cmds.append(
            "git config -f .gitmodules submodule.{target}.path {path}".format(
                target=target, path=target[2:]
            )
        )
        cmds.append(
            "git config -f .gitmodules submodule.{target}.url {url}".format(
                target=target, url=url
            )
        )
        cmds.append(
            "git config -f .gitmodules submodule.{target}.branch {odoo_version}".format(
                target=target, odoo_version=odoo_version
            )
        )
        cmds.append(
            "git config -f .gitmodules submodule.{target}.shallow true".format(
                target=target
            )
        )
        cmds.append("mkdir -p {target}".format(target=target))
        cmds.append(
            "git -C {target} clone -b {odoo_version} --depth 1 {url} .".format(
                target=target, odoo_version=odoo_version, url=url
            )
        )
        cmd = " && ".join(cmds)
        call_cmd(cmd, echo_cmd=True, exit_on_error=False)


def get_target(repo_url):
    org = os.path.basename(os.path.dirname(repo_url))
    matches = re.search(REPO_REGEXP, repo_url)
    try:
        repo_name = matches.group("repo")
    except (AttributeError, IndexError):
        repo_name = os.path.basename(repo_url).split(".")[0]

    mkdir_p(os.path.join("vendor", org))
    return "./vendor/{org}/{repo_name}".format(org=org, repo_name=repo_name)


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
    "--shallow/--no-shallow",
    default=True,
    help="Do shallow clones by default. (depth=1)",
)
@click.option(
    "--reference-project", required=False, help="Reference project to speed up cloning."
)
@click.option(
    "--is-enterprise",
    is_flag=True,
    default=False,
    prompt="Use Odoo Enterprise (access required)",
    help="Clone enterprise repository (access required).",
)
@click.argument("project", required=True)
def init(odoo_version, shallow, reference_project, is_enterprise, project):
    """ Bootstrap you Odoo project """
    additional_repos = ask_for_additional_repos()
    project = project.lower()  # docker doesn't permit uppercase project names

    click.echo("")
    click.secho("Your choices: ", fg="black", bg="bright_green", bold=True)
    click.echo("")
    click.echo("Reference project: ", nl=False)
    if reference_project:
        shallow = False
        click.secho(reference_project, fg="yellow", bold=True)

    else:
        click.secho("None", fg="yellow", bold=True)

    click.echo("Clone depth:       ", nl=False)
    if shallow:
        click.secho("1", fg="yellow", bold=True)
    else:
        click.secho("Full", fg="yellow", bold=True)

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

    # Make sure basic stuff is there
    if not find_executable("make"):
        install_make()
    if not find_executable("pre-commit"):
        install_precommit()
    install_compose_impersonation()

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
        clone_target(
            odoo_version, repo_url, get_target(repo_url), shallow, reference_project
        )
    clone_target(
        odoo_version,
        "https://github.com/odoo/odoo.git",
        "./vendor/odoo/cc",
        shallow,
        reference_project,
    )
    if is_enterprise:
        clone_target(
            odoo_version,
            "https://github.com/odoo/enterprise.git",
            "./vendor/odoo/ee",
            shallow,
            reference_project,
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

    call_cmd("pre-commit install")
    click.echo(
        "Next, run: " + click.style("`cd {} && make info`".format(project), fg="yellow")
    )


if __name__ == "__main__":
    init()
