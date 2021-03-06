import os

import click
import networkx
from networkx import ancestors, bidirectional_shortest_path, dag_longest_path, subgraph

from ._helpers import call_cmd, get_fs_target
from ._modulegraph import get_graph

DOCKERIGNORE_PLACEHOLDER = "# Autogenerated file content from here ... DO NOT MODIFY"


def _get_sparse_persistence_file(ns):
    return os.path.abspath(os.path.join(ns, "..", ".sparse-" + os.path.basename(ns)))


def _get_ns_from_sparse_persistence_file(ns_path):
    # Get from vendor downstream
    path = "".join(ns_path.partition("vendor")[1:])
    return os.path.join(os.path.dirname(path), os.path.basename(path)[8:])


def _get_sparse_file(ns):
    git_path = call_cmd(
        "git rev-parse --git-dir", echo_cmd=False, exit_on_error=False, cwd=ns
    )
    return os.path.join(git_path, "info", "sparse-checkout")


def _symlink_sparse_file(ns):
    ns_path = _get_sparse_persistence_file(ns)
    sparse_file = _get_sparse_file(ns)
    call_cmd(
        "ln -s {ns_path} {sparse_file}".format(**locals()), exit_on_error=False, cwd=ns
    )


def _log_longest_path_per_module(module, g, deps):
    sub = subgraph(g, deps)
    predecessors = set(g.predecessors(module))
    click.secho(module + ": ", fg="green", bold=True, nl=False)
    click.secho(", ".join(predecessors), fg="yellow")
    click.secho(
        "Shortest: " + " > ".join(bidirectional_shortest_path(g, "base", module)),
        fg="white",
    )
    click.secho("Longest:  " + " > ".join(dag_longest_path(sub)), fg="white")
    click.secho("All Deps: " + ", ".join(sorted(list(deps - predecessors))), fg="white")


def ensure_sparse_checkouts(rootpath):
    for root, _, files in os.walk(rootpath):
        for file in files:
            if file.startswith(".sparse-"):
                ns = os.path.join(root, file[8:])
                _symlink_sparse_file(ns)
                call_cmd(
                    "git config core.sparseCheckout True", exit_on_error=False, cwd=ns
                )
                call_cmd("rm -rf *", exit_on_error=False, cwd=ns)
                call_cmd("git reset --hard HEAD", exit_on_error=False, cwd=ns)


def _get_all_sparse_files(g):
    sparse_files = set()
    for module in g:
        node = g.node[module]
        if not node:
            continue
        ns = node["namespace"]
        ns_path = _get_sparse_persistence_file(ns)
        if os.path.isfile(ns_path):
            sparse_files |= {ns_path}
    return sorted(sparse_files)


def _warn_missing_dependencies(g, rootpath):
    for module in g:
        node = g.node[module]
        if not node:
            succ = g.successors(module)
            click.secho(
                "DEPENDENCY INFO: '{}' used by '{}' was NOT found anywhere "
                "under {}.".format(module, ", ".join(succ), rootpath),
                fg="yellow",
                bold=True,
            )


def _write_to_sparse_file(ns, include, must_exist=True):
    ns_path = _get_sparse_persistence_file(ns)
    existing = set()
    if os.path.isfile(ns_path):
        with open(ns_path, "r") as f:
            existing = set(f.read().splitlines())
    elif must_exist:
        return False
    if not include - existing:
        return False

    should = include | existing
    # Make sure setup exepmtion is the last item
    if "!setup/**" in should:
        should.remove("!setup/**")
    with open(ns_path, "w") as f:
        f.write("\n".join(should) + "\n!setup/**\n")
    return True


def _reconcile_auto_install(g):
    all_sparse_files = _get_all_sparse_files(g)
    all_white_listed = []
    auto_install = []
    for module in g:
        node = g.node[module]
        if not node:
            continue
        ns = node["namespace"]
        ns_path = _get_sparse_persistence_file(ns)
        if not os.path.isfile(ns_path):
            all_white_listed.append(module)
        if node["manifest"].get("auto_install"):
            auto_install.append(module)

    for f_path in all_sparse_files:
        with open(f_path, "r") as f:
            all_white_listed.extend(f.read().splitlines())

    state_change = False
    for module in auto_install:
        node = g.node[module]
        if not node:
            continue
        deps = node["manifest"].get("depends", [])
        if not all(dep in all_white_listed for dep in deps):
            continue

        # If no sparse-persistence file exists, no need to whitelist, either.
        ns = node["namespace"]
        state_change = _write_to_sparse_file(ns, {module})
    return state_change


def ensure_dockerignore_updated(g):
    all_sparse_files = _get_all_sparse_files(g)
    dockerignore_snippet = ""
    for file in all_sparse_files:
        ns = _get_ns_from_sparse_persistence_file(file)
        ignore = [os.path.join(ns, "**")]
        with open(file, "r") as f:
            existing = set(f.read().splitlines())
        less = ["!" + os.path.join(ns, l) for l in existing if "!setup" not in l]
        dockerignore_snippet += "\n".join(ignore + sorted(less)) + "\n"

    with open(".dockerignore", "r") as f:
        lines = f.read().splitlines()

    with open(".dockerignore", "w") as f:
        for line in lines:
            f.write(line + "\n")
            if DOCKERIGNORE_PLACEHOLDER in line:
                break
        f.write(dockerignore_snippet)


def _handle_module(g, module, rootpath, skip_native):
    try:
        deps = ancestors(g, module)
    except networkx.exception.NetworkXError:
        click.secho(
            "UNKNOWN MODULE: '{}' is not in the module graph built from "
            "{}.".format(module, rootpath),
            fg="red",
            bold=True,
        )
        click.get_current_context().exit(code=1)

    node = g.node[module]
    if not node:
        click.secho(
            "MISSING MODULE, BUT REFERENCED: While '{}' is itself listed as a "
            "dependency somewhere, it was found nowhere under "
            "{}.".format(module, rootpath),
            fg="red",
            bold=True,
        )
        click.get_current_context().exit(code=1)

    _log_longest_path_per_module(module, g, deps)

    if skip_native and "vendor/odoo" in node["namespace"]:
        click.get_current_context().exit(
            "You have specified a native module while skipping native modules "
            "from whitelisting."
        )

    # src folder modules should not be white listed
    if "src" in node["namespace"]:
        include = {}
    else:
        include = {node["namespace"]: {module}}

    fail = False
    for dep in deps:
        node = g.node[dep]
        if not node:
            fail = True
            click.secho(
                "MISSING DEPENDENCY: The dependency '{}' was found nowhere "
                "under {}.".format(dep, rootpath),
                fg="red",
                bold=True,
            )
            continue
        ns = node["namespace"]
        if skip_native and "vendor/odoo" in node["namespace"]:
            continue
        # src folder dependencies should not be white listed
        if "src" in node["namespace"]:
            continue
        include.setdefault(ns, set())
        include[ns] |= {dep}
    if fail:
        click.get_current_context().exit(code=1)

    for ns in include.keys():
        _write_to_sparse_file(ns, include[ns], must_exist=False)


@click.command()
@click.option(
    "--skip-native",
    is_flag=True,
    default=True,
    prompt="Ignore native modules from sparse checkout config?",
    help="Excludes native modules form sparse checkout configuration.",
)
@click.argument("module", required=False)
def whitelist(module, skip_native):
    """ Whitleist a module dependency tree for sparse checkout. If no module is
     specified, whitelist all depedencies of all modules listed in ./src."""

    # We are inside of a git
    if not (
        call_cmd(
            "git rev-parse --is-inside-work-tree", exit_on_error=False, echo_cmd=False
        )
        == "true"
    ):
        click.get_current_context().fail("You are not inside a work tree.")

    # Validate we are in the right folder (~/odoo/org/project)
    repo_url = call_cmd("git config --local remote.origin.url", echo_cmd=False)
    if not repo_url:
        click.get_current_context().fail(
            "This project has no origin repo (yet). Please configure an origin "
            "first before continuing with white listing operations."
        )
    top_level = call_cmd("git rev-parse --show-toplevel", echo_cmd=False)
    expected_path = get_fs_target(repo_url)
    if expected_path != top_level:
        click.get_current_context().fail(
            "How you dare not to stick with the odooup folder convention? "
            "This project is expected to live in {}".format(expected_path)
        )

    click.secho(
        "Note: graph is analyised against commited state, NOT the working "
        "directory or index!\n",
        fg="green",
        bold=True,
    )
    # Start white listing
    g = get_graph(top_level)
    # If no module is set, whitelist based on src folder
    if not module:
        for module in g:
            node = g.node[module]
            if "namespace" in node and "src" in node["namespace"]:
                _handle_module(g, module, top_level, skip_native)
    else:
        _handle_module(g, module, top_level, skip_native)

    while _reconcile_auto_install(g):
        pass

    ensure_sparse_checkouts(top_level)

    ensure_dockerignore_updated(g)

    _warn_missing_dependencies(g, top_level)


if __name__ == "__main__":
    whitelist()
