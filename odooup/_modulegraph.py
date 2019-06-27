# Copyright (c) 2015-2018 ACSONE SA/NV
# Copyright (c) 2019 XOE Corp. SAS
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import ast
import os

import networkx as nx


class ManifestContainer(object):
    pass


MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")


class NoManifestFound(Exception):
    pass


def _get_manifest_path(addon_dir):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = os.path.join(addon_dir, manifest_name)
        if os.path.isfile(manifest_path):
            return manifest_path


def _parse_manifest(s):
    return ast.literal_eval(s)


def _read_manifest(addon_dir):
    manifest_path = _get_manifest_path(addon_dir)
    if not manifest_path:
        raise NoManifestFound("no Odoo manifest found in %s" % addon_dir)
    with open(manifest_path) as mf:
        return _parse_manifest(mf.read())


def _find_addons(dir):
    """ yield (addon_name, addon_dir, manifest) """
    for root, _, files in os.walk(dir):
        if any(M in files for M in MANIFEST_NAMES):
            yield os.path.dirname(root), os.path.basename(root), _read_manifest(root)


def get_graph(dir):
    g = nx.DiGraph()
    for namespace, name, manifest in _find_addons(dir):
        g.add_node(name, manifest=manifest, namespace=namespace)
        edges = zip(
            manifest.get("depends", []), [name] * len(manifest.get("depends", []))
        )
        g.add_edges_from(edges)
    return g
