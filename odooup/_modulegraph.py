# Copyright (c) 2015-2018 ACSONE SA/NV
# Copyright (c) 2019 XOE Corp. SAS
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import ast
import os

import click
import networkx as nx

from ._helpers import call_cmd

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")
SKIP_PATHS = ["point_of_sale/tools"]


def _get_manifest_from_git(repo_path, manifest_object):
    return call_cmd(
        "git cat-file -p {manifest_object}".format(**locals()),
        echo_cmd=False,
        exit_on_error=False,
        cwd=repo_path,
    )


def _find_addons(dir):
    """ yield (addon_dir, addon_name, manifest) """
    project = call_cmd(
        "git ls-tree -r HEAD", echo_cmd=False, exit_on_error=False, cwd=dir
    ).split("\n")
    project = [i.split() for i in project]
    project_submodule_paths = [i[3] for i in project if i[1] == "commit"]
    manifests = {}

    def _get_module_name(manifest_path):
        return os.path.basename(os.path.dirname(manifest_path))

    # First iterate on submodules in reversed alphabetical
    # order (same as DockeryOdoo) -- for drop in module overrides
    for submodule_path in reversed(sorted(project_submodule_paths)):
        submodule = call_cmd(
            "git ls-tree -r HEAD",
            echo_cmd=False,
            exit_on_error=False,
            cwd=submodule_path,
        ).split("\n")
        submodule = [i.split() for i in submodule]
        manifests.update(
            {
                _get_module_name(i[3]): (  # module name
                    submodule_path,  # submodule base path
                    i[2],  # manifest object
                    os.path.join(submodule_path, i[3]),  # full manifest path
                )
                for i in submodule
                if i[1] == "blob"
                and any(M in i[3] for M in MANIFEST_NAMES)
                and not any(S in i[3] for S in SKIP_PATHS)
            }
        )
    # Always give src highest priority
    manifests.update(
        {
            _get_module_name(i[3]): (  # module name
                ".",  # relative to root repo path
                i[2],  # manifest object
                i[3],  # full manifest path
            )
            for i in project
            if i[1] == "blob"
            and any(M in i[3] for M in MANIFEST_NAMES)
            and not any(S in i[3] for S in SKIP_PATHS)
        }
    )
    for module, (repo_path, manifest_object, manifest_path) in manifests.items():
        module_path = os.path.dirname(manifest_path)

        try:
            manifest_str = _get_manifest_from_git(repo_path, manifest_object)
            manifest = ast.literal_eval(manifest_str)
        except SyntaxError:
            click.secho("Error Parsing: {}".format(module_path), fg="yellow")
            continue
        yield os.path.dirname(module_path), module, manifest


def get_graph(dir):
    g = nx.DiGraph()
    for namespace, name, manifest in _find_addons(dir):
        g.add_node(name, manifest=manifest, namespace=namespace)
        edges = zip(
            manifest.get("depends", []), [name] * len(manifest.get("depends", []))
        )
        g.add_edges_from(edges)
    return g
