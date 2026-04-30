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
     - Defines the ``Point`` message — a 3D Cartesian coordinate (``x``, ``y``,
       ``z`` as ``double``) used by the Reduction service for geometric results
       such as centroid, force, and moment.
   * - :doc:`SchemePointer <scheme_pointer>`
     - Typed value container used to exchange Scheme-typed data between the
       client and Fluent's Scheme runtime.
   * - :doc:`Variant <variant>`
     - Polymorphic value container (bool, int64, double, string, vectors, or
       map) passed as arguments and returned from DataModel RPCs.

.. toctree::
   :hidden:
   :maxdepth: 2

   primitives
   scheme_pointer
   variant
