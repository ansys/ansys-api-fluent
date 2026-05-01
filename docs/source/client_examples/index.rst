.. _client_examples:

======================
Python client examples
======================

End-to-end Python recipes for talking to a running Fluent server using the
generated proto stubs in ``ansys.api.fluent.v1``. Each page introduces a
service or helper module, walks through its RPCs with annotated code samples,
and links to the corresponding entry in the :ref:`api_reference` for the
complete message and field listing.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Section
     - Contents
   * - :doc:`Services <services/index>`
     - Worked Python examples for the eleven gRPC services that make up the
       current Fluent API.
   * - :doc:`Helper modules <helpers/index>`
     - Usage examples for the shared protobuf message types referenced across
       multiple services.
   * - :doc:`Legacy <legacy/index>`
     - Examples for older services retained for backward compatibility.

.. toctree::
   :hidden:
   :maxdepth: 2

   services/index
   helpers/index
   legacy/index
