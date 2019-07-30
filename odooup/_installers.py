# -*- coding: utf-8 -*-
import os
import platform
from distutils.spawn import find_executable

import click

from ._helpers import call_cmd


def check_versions():
    try:
        git_ok = (
            call_cmd("git version", exit_on_error=False, echo_cmd=False)
            >= "git version 2.22.0"
        )
    except Exception:
        git_ok = False
    if not git_ok:
        click.get_current_context().fail(
            "Please install git version > 2.22.0.\n"
            "In debian, you can do:\n"
            "\t$ sudo add-apt-repository ppa:git-core/ppa -y\n"
            "\t$ sudo apt-get update\n"
            "\t$ sudo apt-get install --upgrade git -y\n"
        )
    try:
        docker_ok = (
            call_cmd("docker --version", exit_on_error=False, echo_cmd=False).split(
                ","
            )[0]
            >= "Docker version 18.09.6"
        )
    except Exception:
        docker_ok = False
    if not docker_ok:
        click.get_current_context().fail(
            "Please install docker version >= 18.09.6.\n"
            "Follow instructions from \n"
            "\thttps://docs.docker.com/install/linux/docker-ce/ubuntu/"
        )
    try:
        docker_compose_ok = (
            call_cmd(
                "docker-compose --version", exit_on_error=False, echo_cmd=False
            ).split(",")[0]
            >= "docker-compose version 1.21.0"
        )
    except Exception:
        docker_compose_ok = False
    if not docker_compose_ok:
        click.get_current_context().fail(
            "Please install docker-compose version >= 1.21.0.\n"
            "Follow instructions from \n"
            "\thttps://docs.docker.com/compose/install/"
        )


def install_make():
    click.secho("We need to install make ...\n", fg="red")
    if platform.system() != "Windows":
        if not find_executable("apt"):
            click.get_current_context().fail(
                "Can't find apt package manager. Please install make manually."
            )
        call_cmd("sudo -k -H apt install make")
    else:
        click.get_current_context().fail(
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
        if not find_executable("pip"):
            click.get_current_context().fail(
                "Can't find pip python package manager. Please install pip manually."
            )
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
    check_versions()
    # Make sure basic stuff is there
    if not find_executable("make"):
        install_make()
    if not find_executable("pre-commit"):
        install_precommit()
    install_compose_impersonation()
