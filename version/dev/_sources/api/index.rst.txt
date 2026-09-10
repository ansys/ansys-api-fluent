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
       :doc:`Health <services/health>`,
       :doc:`ApplicationRuntime <services/application_runtime>`,
       :doc:`DataModel <services/object_model>`,
       :doc:`Settings <services/settings>`,
       :doc:`Events <services/events>`,
       :doc:`FieldData <services/field_data>`,
       :doc:`Monitor <services/monitor>`,
       :doc:`Reduction <services/reduction>`,
       :doc:`SolutionVariable <services/solution_variable>`,
       :doc:`Transcript <services/transcript>`, and
       :doc:`Connection <services/connection>`.
   * - :doc:`Helper modules <helpers/index>`
     - Shared protobuf message types used as fields across multiple services:
       :doc:`Primitives <helpers/primitives>`,
       :doc:`SchemePointer <helpers/scheme_pointer>`, and
       :doc:`Variant <helpers/variant>`.
   * - :doc:`Legacy <legacy/index>`
     - Older services retained for backward compatibility:
       :doc:`TextInterface <legacy/text_interface>` and
       :doc:`SchemeInterpreter <legacy/scheme_interpreter>`. Prefer the current
       service equivalents for new work.

.. toctree::
   :hidden:
   :maxdepth: 2

   services/index
   helpers/index
   legacy/index
