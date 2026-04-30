.. _api_reference:

=============
API reference
=============

Complete RPC reference for the Fluent gRPC API (``ansys.api.fluent.v1``).
Each service page lists all RPCs together with their request/response message
fields and field constraints. Helper modules document shared message types
referenced across services.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Section
     - Contents
   * - :doc:`Services <services/index>`
     - The eleven gRPC services that make up the current Fluent API:
       ``Health``, ``AppUtilities``, ``DataModelSE``, ``Settings``,
       ``Events``, ``FieldData``, ``Monitor``, ``Reduction``, ``Svar``,
       ``Transcript``, and ``Connection``.
   * - :doc:`Helper modules <helpers/index>`
     - Shared protobuf message types (``Primitives``, ``SchemePointer``,
       ``Variant``) used as fields across multiple services.
   * - :doc:`Legacy <legacy/index>`
     - Older services (``TextInterface``, ``SchemeInterpreter``) retained for
       backward compatibility. Prefer the current service equivalents for new
       work.

.. toctree::
   :hidden:
   :maxdepth: 2

   services/index
   helpers/index
   legacy/index
