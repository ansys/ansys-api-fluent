Helper modules
==============

This section documents shared protobuf message types that are referenced by
multiple Fluent services. They are support modules, not standalone gRPC
services, and are listed separately to keep service pages focused on RPC
workflows.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Module
     - Purpose
   * - :doc:`Primitives <primitives>`
     - Common scalar and composite data structures (``StringPair``,
       ``StrIntPair``, ``Chunk``, etc.) shared across multiple service protos.
   * - :doc:`SchemePointer <scheme_pointer>`
     - Typed value container used to exchange Scheme-typed data between the
       client and Fluent's Scheme runtime.
   * - :doc:`Variant <variant>`
     - Polymorphic value container (bool, int, double, string, or list)
       passed as arguments and returned from DataModel and Settings RPCs.

.. toctree::
   :maxdepth: 2

   primitives
   scheme_pointer
   variant
