# `odooup patch` Component

## Abstract

`odooup patch` subcommand takes you back to the fundamentals of patch. It allows
you to "install" patches to your codebase and maintain a remote fork for smooth
upstream contributing conveinience.

It creates PR from your fork to upstream and provides PR headers / footers to
make management of a larg quantity of pull requests a little easier.

It also is build to maintain PR against `master` and do periodic rebases. With
periodic guided backports you can match your current odoo version from your
upstream PR.

Targeting `master` usually significantly increases your chances of acceptance.

## Spec

```
odooup patch [options] <subcommand>
    --origin    Name of odoo-dev upstream to hold PR branches.
    --upstream  Name of odoo upstream to to target PR and fetch updates from.

    --help      This help message

Subcommands:
    update      Update origin, rebase PRs and regenerate local patches - if need
    install     Install a patch from a PR or a github - compare
    apply       Apply all "installed" patches onto the current working dir

    All options can be supplied with environment variables:
        Uppercase / strip inital '--' / replace '-' by '_' / prefix `ODOOUP_`.
```


<div align="center">
    <div>
        <a href="https://xoe.solutions">
            <img width="100" src="https://erp.xoe.solutions/logo.png" alt="XOE Corp. SAS">
        </a>
    </div>
    <p>
    <sub>Currently, folks <a href="https://github.com/xoe-labs/">@xoe-labs</a> try to keep up with their task to maintain this.</sub>
    </p>
    <p>
    <sub>If you're the kind of person, willing to sponsor open source projects, consider sending some spare XLM banana to <code>blaggacao*keybase.io</code></sub>
    </p>
</div>
