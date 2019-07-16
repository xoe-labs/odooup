import os

import appdirs

from ._helpers import call_cmd, mkdir_p


def construe_git_url(prefix, host, org, project):
    """construe a git url from it's parts"""
    sep = ":" if prefix.startswith("git") else "/"
    return prefix + host + sep + org + "/" + project  # + '.git'


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
