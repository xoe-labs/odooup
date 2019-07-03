# Copyright (c) 2015-2018 ACSONE SA/NV
# Copyright (c) 2019 XOE Corp. SAS
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import ast
import os

import networkx as nx

from ._helpers import call_cmd

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")
SKIP_PATHS = ["point_of_sale/tools"]


def _parse_manifest_from_git(repo_path, manifest_object):
    s = call_cmd(
        "git cat-file -p {manifest_object}".format(**locals()),
        echo_cmd=False,
        exit_on_error=False,
        cwd=repo_path,
    )
    return ast.literal_eval(s)


def _find_addons(dir):
    """ yield (addon_dir, addon_name, manifest) """
    project = call_cmd(
        "git ls-tree -r HEAD", echo_cmd=False, exit_on_error=False, cwd=dir
    ).split("\n")
    project = [i.split() for i in project]
    manifests = {
        (".", i[2], i[3])
        for i in project
        if i[1] == "blob"
        and any(M in i[3] for M in MANIFEST_NAMES)
        and not any(S in i[3] for S in SKIP_PATHS)
    }
    project_submodule_paths = [i[3] for i in project if i[1] == "commit"]
    for path in project_submodule_paths:
        submodule = call_cmd(
            "git ls-tree -r HEAD", echo_cmd=False, exit_on_error=False, cwd=path
        ).split("\n")
        submodule = [i.split() for i in submodule]
        manifests |= {
            (path, i[2], os.path.join(path, i[3]))
            for i in submodule
            if i[1] == "blob" and any(M in i[3] for M in MANIFEST_NAMES)
        }
    for repo_path, manifest_object, manifest_path in manifests:
        module_path = os.path.dirname(manifest_path)
        manifest = _parse_manifest_from_git(repo_path, manifest_object)
        yield os.path.dirname(module_path), os.path.basename(module_path), manifest


def get_graph(dir):
    g = nx.DiGraph()
    for namespace, name, manifest in _find_addons(dir):
        g.add_node(name, manifest=manifest, namespace=namespace)
        edges = zip(
            manifest.get("depends", []), [name] * len(manifest.get("depends", []))
        )
        g.add_edges_from(edges)
    return g
