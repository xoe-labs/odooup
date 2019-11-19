# `odooup conform` Component

## Abstract

`odooup conform` subcommand helps conforming your code base to "X", where "X"
can be a new code verion or alternatively odoo-pylint and the like.

Conformance tarets are implemented by calls to packages, libraries or scripts.

For peace-of-mind code refactorings, [pybowler](https://pybowler.io/) scripts
are mostly a good choice to implement specific code conformance targets.

## Spec

```
odooup conform [options] <codedir>
    --to-v13    Apply refactorings to conform to Odoo v13 code standard
    --to-v12    Apply refactorings to conform to Odoo v12 code standard
    --to-v11    Apply refactorings to conform to Odoo v11 code standard
    --to-C8104  Apply refactorings to conform to Odoo Pylint C8104 check
    ...

    --help      This help

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
