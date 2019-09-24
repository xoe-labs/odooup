Changes
~~~~~~~

.. Future (?)
.. ----------
.. -

0.1.1 (2019-05-14)
------------------
- Fix global src modules whitelisting (whitelist without argument)
- Add more useful dependency logs (no more longest dep warning)
- Add more useful dependency logs (show successors of missing deps)
- Fix autoinstall whitlisted modules

0.1.0 (2019-05-14)
------------------
- Be forgiving on non parsable manifests for dep whitelisting

[...]
-----

0.0.4 (2019-05-14)
------------------
Fixed
^^^^^
- Fix shallow submodules for any version of Odoo

0.0.3 (2019-05-02)
------------------
Fixed
^^^^^
- Fix duplicated tag "{BACKPORT_FLAG}-{TAG}"
- Fix error passing candidate as a tuple backporting a specific commit

0.0.1 (2019-04-18)
------------------
- Carve out functionality from dockery-odoo-scaffold hack
- init: helper to initialize an odoo project
- repo: toolset to manage your own odoo-dev / patches
