# -*- coding: utf-8 -*-
import errno
import os
import subprocess

import click


def call_cmd(cmd, echo_cmd=True, exit_on_error=True):
    if echo_cmd:
        click.secho(cmd, fg="green")
    try:
        result = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True
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
