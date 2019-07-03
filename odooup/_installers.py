# -*- coding: utf-8 -*-
import os
import platform
from distutils.spawn import find_executable

import click

from ._helpers import call_cmd


def install_make():
    click.secho("We need to install make ...\n", fg="red")
    if platform.system() != "Windows":
        call_cmd("sudo -k -H apt install make")
    else:
        click.fail(
            "As a windows user, you must install `make` manually. "
            "See: http://bfy.tw/NI8r"
        )


def install_precommit():
    click.secho(
        "We install a bunch of pre-commit.com hooks"
        "to help you produce better code ...\n",
        fg="red",
    )
    if platform.system() != "Windows":
        call_cmd("sudo -k -H pip install pre-commit")
    else:
        call_cmd("pip install pre-commit")


def install_compose_impersonation():
    if platform.system() != "Linux":
        # Docker for X does handle user mapping for us
        return

    compose_impersonation = os.getenv("COMPOSE_IMPERSONATION")
    if not compose_impersonation:
        compose_impersonation = "{}:{}".format(os.getuid(), os.getgid())
        os.putenv("COMPOSE_IMPERSONATION", compose_impersonation)
        os.environ["COMPOSE_IMPERSONATION"] = compose_impersonation
        try:
            with open(os.path.realpath(os.path.expanduser("~/.bashrc")), "a") as file:
                file.write(
                    "\nexport COMPOSE_IMPERSONATION='{COMPOSE_IMPERSONATION}'\n".format(
                        COMPOSE_IMPERSONATION=compose_impersonation
                    )
                )
        except IOError:
            click.secho(
                "Failed adding following line to {}:\n\t "
                "export COMPOSE_IMPERSONATION='{}'\n "
                "Please add it manually for full feature support.".format(
                    os.path.realpath(os.path.expanduser("~/.bashrc")),
                    compose_impersonation,
                ),
                fg="red",
            )


def install_tools():
    # Make sure basic stuff is there
    if not find_executable("make"):
        install_make()
    if not find_executable("pre-commit"):
        install_precommit()
    install_compose_impersonation()
