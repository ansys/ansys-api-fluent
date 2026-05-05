.. _client_examples:

======================
Python client examples
======================

End-to-end Python recipes for talking to a running Fluent server using the
generated proto stubs in ``ansys.api.fluent.v1``. Each page walks through RPC
workflows with annotated code samples and links to the :ref:`api_reference`
for complete message and field listings.

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Page
     - Contents
   * - :doc:`Health <health>`
     - Readiness probe — verify the server is accepting requests before issuing
       any other RPC.
   * - :doc:`ApplicationRuntime <app_utilities>`
     - Version and build metadata, process information, Python journal
       recording, and feature flag management.
   * - :doc:`DataModel <datamodel_se>`
     - Structured read/write access to Fluent's object tree, addressed by a
       rules context and a slash-separated path.
   * - :doc:`Settings <settings>`
     - Hierarchical read/write access to simulation configuration — boundary
       conditions, solver controls, model parameters, and results settings.
   * - :doc:`Events <events>`
     - Server-streamed notifications for solver lifecycle and residual
       convergence events.
   * - :doc:`FieldData <field_data>`
     - Streams scalar fields, vector fields, surface geometry, mesh topology,
       pathlines, and particle tracks from a live session.
   * - :doc:`Monitor <monitor>`
     - Query monitor metadata and stream live monitor data during a simulation.
   * - :doc:`Reduction <reduction>`
     - Scalar and vector reduction operations over solution fields.
   * - :doc:`SolutionVariable <svar>`
     - Per-zone solution variable access — read raw solver arrays or write
       modified values back into the solver.
   * - :doc:`Transcript <transcript>`
     - Streams Fluent console output to the client as a continuous server-side
       stream.
   * - :doc:`Connection <connection>`
     - Manages client connections to Fluent servers.
   * - :doc:`Helper types <helpers>`
     - Usage examples for the shared protobuf message types (``Variant`` and
       ``Point``) referenced across multiple services.

.. toctree::
   :hidden:
   :maxdepth: 2

   health
   app_utilities
   datamodel_se
   settings
   events
   field_data
   monitor
   reduction
   svar
   transcript
   connection
   helpers
