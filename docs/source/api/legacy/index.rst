.. _legacy:

======
Legacy
======

These services are retained for backward compatibility. They remain fully
functional but are superseded by current equivalents — prefer
:doc:`DataModel <../services/datamodel_se>` over ``TextInterface`` and
:doc:`Settings <../services/settings>` or the :doc:`SchemePointer
<../helpers/scheme_pointer>` helper over ``SchemeInterpreter`` for new work.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Service
     - Purpose
   * - :doc:`TextInterface <datamodel_tui>`
     - Structured access to Fluent's TUI datamodel — query the command
       hierarchy, retrieve documentation, and execute TUI commands.
   * - :doc:`SchemeInterpreter <scheme_eval>`
     - Execute and evaluate Scheme expressions inside a running Fluent session.

.. toctree::
   :hidden:
   :maxdepth: 2

   datamodel_tui
   scheme_eval
