# -*- coding: utf-8 -*-
import errno
import os
import re
import subprocess

import click

REPO_REGEXP = r"(?P<prefix>git@|https://)(?P<host>[\w\.@]{1,})(/|:)(?P<org>[\w,\-,_]{1,})/(?P<project>[\w,\-,_]{1,})(.git){0,1}((/){0,1})"  # noqa


def call_cmd(cmd, echo_cmd=True, exit_on_error=True, cwd=None):
    if echo_cmd:
        if cwd:
            click.echo("Do in: " + click.style(cwd, fg="yellow"))
        click.secho(("\t" if cwd else "") + cmd, fg="green")
    try:
        result = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True, cwd=cwd
        )
    except subprocess.CalledProcessError as exc:
        if exit_on_error:
            click.secho(str(exc.output).strip(), fg="red")
            exit(exc.returncode)
        result = "ERROR"
    return result.strip()


def replace_in_file(files, from_str, to_str):
    if not isinstance(files, (list, tuple)):
        files = [files]
    for file_path in files:
        data = open(file_path).read()
        new_data = data.replace(from_str, to_str)
        if data != new_data:
            with open(file_path, "w") as file:
                file.write(new_data)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if not (exc.errno == errno.EEXIST and os.path.isdir(path)):
            raise


def construe_git_url(prefix, host, org, project):
    """construe a git url from it's parts"""
    sep = ":" if prefix.startswith("git") else "/"
    return prefix + host + sep + org + "/" + project  # + '.git'


class NotAGitURL(RuntimeError):
    pass


def parse_git_url(url):
    """get the parts of a git url"""
    matches = re.search(REPO_REGEXP, url)
    try:
        prefix = matches.group("prefix")
        host = matches.group("host")
        org = matches.group("org")
        project = matches.group("project")
    except (AttributeError, IndexError):
        raise NotAGitURL()
    return prefix, host, org, project
