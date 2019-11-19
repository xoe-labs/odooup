# `odooup mask` Component

## Abstract

`odooup mask` subcommand leverages advanced git and docker primitives to mask
odoo modules from checkout and building. This let's you whitelist a well-defined
module set for your odoo project, including stock odoo modules.

It leverages sparse checkout and analises the git database directly in order to
present an eventually consistent user interface to git sparce-checkouts.

Sparse checkouts are a little used, powerful beast & they are standard `git`.

## Spec

```
odooup mask [options] <projectname>
    --no-skip-native    Don't skip native CC & EE modules from masking.

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
