import os
import re

import appdirs

from ._helpers import call_cmd, mkdir_p

REPO_REGEXP = r"(?P<prefix>git@|https://)(?P<host>[\w\.@]{1,})(/|:)(?P<org>[\w,\-,_,/]{1,})/(?P<project>[\w,\-,_]{1,})(.git){0,1}((/){0,1})"  # noqa


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


def cache_repo(prefix, host, org, project):
    """ Cache repo locally (or update cache) """
    # init cache directory

    cache_dir = appdirs.user_cache_dir("odooup")
    repo_cache_dir = os.path.join(cache_dir, host, org.lower(), project.lower())

    if not os.path.isdir(repo_cache_dir):
        mkdir_p(repo_cache_dir)
        cmd = ["git", "init", "--bare"]
        call_cmd(" ".join(cmd), echo_cmd=False, exit_on_error=True, cwd=repo_cache_dir)
    repo_url = construe_git_url(prefix, host, org, project)
    # fetch all branches into cache
    cmd = ["git", "fetch", "--quiet", "--force", repo_url, "refs/heads/*:refs/heads/*"]
    call_cmd(" ".join(cmd), echo_cmd=True, exit_on_error=True, cwd=repo_cache_dir)
    return repo_cache_dir
