#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# This file is part of the dodoo-tester (R) project.
# Copyright (c) 2018 XOE Corp. SAS
# Authors: David Arnold, et al.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division

import subprocess

import click
from future import standard_library

standard_library.install_aliases()


BACKPORT_FLAG = "BACKPORT"
BASE_BRANCHES = ["6.0", "6.1", "7.0", "8.0", "9.0", "10.0", "11.0", "12.0", "master"]
PATCH_PREFIX = "{}/{}-".format
PATCH_FORMAT = "{}/{}-{}".format
BASE_FORMAT = "{}/{}".format
COMPILED_FORMAT = "{}/compiled/{}".format


class Git(object):
    def __enter__(self):
        self.head = self.get_branch_name()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.run(["checkout", self.head])

    def __init__(self, git_dir, remote, branches=None):
        self.git_dir = git_dir
        self.remote = remote
        self.branches = branches or []
        self.head = None
        click.echo("==> Git-Dir: %s" % self.git_dir)
        click.echo("==> Remote: %s" % self.remote)
        if self.branches:
            click.echo("==> Base-Branche(s): %s" % ",".join(self.branches))

    def _add_branches(self, branches):
        self.branches = self.branches + branches
        click.echo("==> Base-Branche(s): %s" % ",".join(self.branches))

    def run(self, command):
        """Execute git command in bash
        :param list command: Git cmd to execute in self.git_dir
        :return: String output of command executed.
        """
        cmd = ["git", "--git-dir=" + self.git_dir] + command
        try:
            click.echo(">>> " + " ".join(cmd))
            res = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            res = None
        if isinstance(res, bytes):
            res = res.decode("utf-8")
        if res:
            res = res.strip("\n")
        return res

    def _continue_or_abort(self, op):
        if click.confirm("Continue (or abort)?"):
            if self.run([op, "--continue"]) is None:
                return self._continue_or_abort(op)
            return True
        else:
            self.run([op, "--abort"])
            return False

    def checkout(self, branch, new=None):
        if new:
            res = self.run(["checkout", "-b", new, branch])
        else:
            res = self.run(["checkout", branch])
        if res is None:
            click.get_current_context().fail("Checkout failed. Aborting for security.")

    def rebase(self, branch, base_branch):
        if self.run(["rebase", base_branch, branch]) is None:
            click.echo("After resolving rebase conflicts manually:")
            return self._continue_or_abort("rebase")
        else:
            return True

    def cherry_pick(self, commits):
        if self.run(["cherry-pick"] + commits) is None:
            click.echo("After resolving cherry-pick conflicts manually:")
            return self._continue_or_abort("cherry-pick")
        else:
            return True

    def merge(self, branch):
        if self.run(["merge", "--no-ff", branch]) is None:
            click.echo("After resolving merge conflicts manually:")
            return self._continue_or_abort("merge")
        else:
            return True

    def cherry(self, source, target):
        res = self.run(["cherry", target, source])
        return res.replace("+ ", "").split("\n")

    def _get_staging_name(self, sstr):
        prefix = self.remote + "/"
        if sstr.startswith(prefix):
            return sstr[len(prefix) :]

    def _get_remote_branches(self):
        return [
            b
            for b in self.run(["branch", "-r"]).replace(" ", "").split("\n")
            if b.startswith(self.remote)
        ]

    def _is_patch(self, branch, base=None):
        base = [base] if base else self.branches

        def _has_prefix(br, b):
            return br.startswith(PATCH_PREFIX(self.remote, b))

        if any(b for b in base if _has_prefix(branch, b)):
            return True

    def update_remote(self):
        """ Updates odoo-dev remote from tracked remote branches """
        click.secho("UPDATE: Running update ...", bg="green", fg="white")
        self.run(["fetch", "--all", "--prune"])
        for branch in self.branches:
            click.secho(
                "UPDATE: %s - Updating local base-branch ..." % branch, fg="green"
            )
            self.checkout(branch)
            self.run(["merge"])
            click.secho("UPDATE: %s - Pushing base-branch ..." % branch, fg="green")
            self.run(["push", self.remote])

    def rebase_patches(self, patchname=None):
        click.secho("REBASE: Rebasing patch branches ...", bg="cyan", fg="white")
        if patchname:
            to_rebase = {
                b: [PATCH_FORMAT(self.remote, b, patchname)] for b in self.branches
            }
        else:
            to_rebase = {b: [] for b in self.branches}
            for br in self._get_remote_branches():
                for base_branch in to_rebase.keys():
                    if self._is_patch(br, base_branch):
                        to_rebase[base_branch].append(br)
        for base_branch, candidates in to_rebase.items():
            for candidate in candidates:
                click.secho("REBASE: %s - Rebasing branch ..." % candidate, fg="cyan")
                staging_name = self._get_staging_name(candidate)
                self.checkout(candidate, staging_name)
                if self.rebase(staging_name, base_branch):
                    click.secho("REBASE: %s - Pushing ..." % candidate, fg="cyan")
                    self.run(["push", "-f", self.remote])
                self.checkout(base_branch)
                self.run(["branch", "-D", staging_name])

    def backport_patches(self, name=None):
        click.secho("BACKPORT: Backporting patch branches ...", bg="cyan", fg="white")

        series = sorted(self.branches)
        while len(series) >= 2:
            remote_branches = self._get_remote_branches()
            from_series = series.pop()
            to_series = series[-1]
            to_backport = []
            for br in remote_branches:
                if name and not br.endswith(name):
                    continue
                if self._is_patch(br, from_series):
                    to_backport.append(br)

            for backport in to_backport:
                click.secho(
                    "BACKPORT: %s - Backporting branch ..." % backport, fg="cyan"
                )
                commits = self.cherry(backport, self.remote + "/" + from_series)
                backport_name = self._backport_name(backport, from_series, to_series)
                staging_backport_name = self._get_staging_name(backport_name)
                self.checkout(self.remote + "/" + to_series, staging_backport_name)
                if self.cherry_pick(commits):
                    click.secho("BACKPORT: %s - Pushing ..." % backport_name, fg="cyan")
                    self.run(["push", "-f", "-u", self.remote, staging_backport_name])
                self.checkout(to_series)
                self.run(["branch", "-D", staging_backport_name])

    def backport_patch(self, refspec, target, name):
        candidate = self.remote + "/-" + name
        backport_name = self._backport_name(candidate, "", target, tag="COMMIT")
        staging_backport_name = self._get_staging_name(backport_name)
        self.checkout(target, staging_backport_name)
        if self.cherry_pick([refspec]):
            click.secho(
                "BACKPORT: {}/{} - Pushing ...".format(
                    self.remote, staging_backport_name
                ),
                fg="cyan",
            )
            self.run(["push", "-f", "-u", self.remote, staging_backport_name])
        self.checkout(target)
        self.run(["branch", "-D", staging_backport_name])

    def compile(self):
        click.secho(
            "COMPILE: Compiling syntetic patch branches ...", bg="blue", fg="white"
        )
        for base_branch in self.branches:
            staging_name = self._get_staging_name(
                COMPILED_FORMAT(self.remote, base_branch)
            )
            self.checkout(BASE_FORMAT(self.remote, base_branch), staging_name)
            click.secho(
                "COMPILE: Preparing syntetic of %s ..." % base_branch, fg="blue"
            )
            for br in self._get_remote_branches():
                if self._is_patch(br, base_branch):
                    click.secho("COMPILE: Merging %s ..." % br, fg="blue")
                    self.merge(br)
            click.secho(
                "COMPILE: Pushing (-f) syntetic of %s ..." % base_branch, fg="blue"
            )
            self.run(["push", "-f", self.remote, staging_name])
            self.checkout(base_branch)
            self.run(["branch", "-D", staging_name])

    def get_branch_name(self):
        """Get branch name
        :return: String with name of current branch name"""
        command = ["rev-parse", "--abbrev-ref", "HEAD"]
        res = self.run(command)
        return res

    def _backport_name(self, candidate, source, target, tag="BRANCH"):
        candidate = candidate.replace(BACKPORT_FLAG + "-" + tag + "-", "")
        return candidate.replace(
            self.remote + "/" + source + "-",
            self.remote + "/" + target + "-" + BACKPORT_FLAG + "-" + tag + "-",
        )


@click.group()
@click.option("--git-dir", default="vendor/odoo/cc/.git", help="Local Repo Git-Dir.")
@click.option("--remote", default="dev", help="Name of odoo-dev remote.")
@click.pass_context
def repo(ctx, git_dir, remote):
    """ Run git commands for custom odoo-dev repository.
    """
    ctx.ensure_object(dict)

    ctx.obj["GIT"] = Git(git_dir, remote)


@repo.command()
@click.option("--update/--no-update", "-u", default=False, help="Update remote repo.")
@click.option("--rebase/--no-rebase", "-r", default=False, help="Rebase patches.")
@click.option(
    "--compile/--no-compile",
    "-c",
    "compile_branch",
    default=False,
    help="Compile consolidated patched branch.",
)
@click.option(
    "--auto/--no-auto", default=False, help="Shorthand for update, rebase, compile."
)
@click.argument("branches", nargs=-1, required=True)
@click.pass_context
def maintain(ctx, update, rebase, compile_branch, auto, branches):
    """ Run maintenance operations on remote development repository.
    """
    git = ctx.obj["GIT"]
    git._add_branches(list(branches))

    if update or auto:
        git.update_remote()
    if rebase or auto:
        git.rebase_patches()
    if compile_branch or auto:
        git.compile()


@repo.group()
@click.pass_context
def backport(ctx):
    """ Run backporting operations.
    """
    pass


@backport.command()
@click.argument("commit", required=True)
@click.argument("target", required=True)
@click.argument("name", required=True)
@click.pass_context
def commit(ctx, commit, target, name):
    """ Backport a single commit from upstream: use for backporting fixes
    not backported in mupstream.

    COMMIT  Refers to the hash value of a cherry-pick commit reference.
    NAME    Refers to the name of the patch without any prefixes.
    TARGET  Refers to the target branch (odoo series) for the final patch.
    """
    git = ctx.obj["GIT"]
    git.backport_patch(commit, target, name)


@backport.command()
@click.argument("name", nargs=1, required=True)
@click.argument("branches", nargs=-1, required=True)
@click.pass_context
def branch(ctx, name, branches):
    """ Backport a patch name backwards between the specified branches.

    NAME        Refers to the name of the patch without any prefixes.
    BRANCHES    Refers to the name of two or more consecutive branches (odoo series).
    """
    git = ctx.obj["GIT"]
    git._add_branches(list(branches))
    git.backport_patches(name=name)


if __name__ == "__main__":
    repo()
