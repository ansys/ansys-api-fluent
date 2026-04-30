.. _legacy:

======
Legacy
======

These services are retained for backward compatibility. They remain fully
functional but are superseded by current equivalents — prefer
:doc:`DataModel <../services/datamodel_se>` over ``TextInterface`` for new
work. The ``SchemeInterpreter`` service itself has no direct modern replacement,
but use its current RPCs (``SchemeEval`` or ``StringEval``) rather than the
deprecated ``Eval`` RPC; see :doc:`SchemePointer <../helpers/scheme_pointer>`
for the helper message type used to construct and read typed Scheme values.

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
