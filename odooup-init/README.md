# `odooup init` Component

## Abstract

`odooup init` subcommand bootstraps a complete odoo project leveraging
[DockeryOdoo](https://github.com/xoe-labs/dockery-odoo) docker images.

It maintains a shared git history with
[dockery-odoo-scaffold](https://github.com/xoe-labs/dockery-odoo-scaffold)
so it's easy (but not always _riskfree_) to pull in latest upstream convenience
changes.

It builds a local git cache for odoo & module remotes, to massively cut cloning
time at project setup, if local cache is already available.

It consistently checks your environment, and spits out useful hints, if you need
to install or upgrade any needed library or tool. Version bumps are conducted
agressively, so expect to be pushed to keep your environment up to date.


## Spec

```
odooup init [options] <projectname>
    --odoo-version         Specify the odoo version to bootstrap.
    --is-enterprise        Clone enterprise repository (access required)
    --upstream-ce          Specify an alternative upstream CE repository.
    --upstream-ee          Specify an alternative upstream EE repository.
    --upstream-scaffold    Specify an alternative upstream scaffold repository.
    --cache                Specify an alternative cache directory.

    --help      This help message

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
