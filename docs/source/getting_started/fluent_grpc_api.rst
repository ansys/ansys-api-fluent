The Fluent gRPC API
===================

This page orients you to the overall structure of the Fluent gRPC API before
you dive into any service-specific detail. Read it once — whether you are
making a single API call or building a client library on top of the API.

What this API gives you
-----------------------

The Fluent gRPC API exposes two complementary, high-level services:

- The **DataModel service** covers multiple Fluent applications, including the
  meshing workflow and the solver object model. It organises Fluent objects as
  a tree addressed by a *rules context* and a slash-separated *path*.

- The **Settings service** covers simulation configuration — boundary
  conditions, solver controls, and results settings. It uses a 
  slash-separated path hierarchy that maps directly to the Fluent settings
  tree.

Both services follow the same two-layer pattern described below. All other
services (Events, Field Data, Health, ApplicationRuntime, etc.) are
single-purpose and do not expose a schema layer.

Two layers: schema and runtime
-------------------------------

Every schema-bearing service — the DataModel service and the Settings service —
exposes two distinct layers:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Layer
     - RPC
     - Purpose
   * - **API schema**
     - ``GetSchema``
     - Returns a static, recursive description of everything that exists at a
       given rules context or settings root: object types, parameter names and
       types, available commands, command arguments, and help text. This is the
       contract. It is independent of any running simulation.
   * - **Runtime**
     - | ``GetState`` / ``SetState`` / ``ExecuteCommand`` (DataModel)
       | ``GetVar`` / ``SetVar`` / ``ExecuteCommand`` (Settings)
     - Read, write, and act on live simulation state. These calls require a
       running Fluent session.

These two layers serve different purposes and different audiences:

- **The API schema layer** is the starting point for anyone building a client
  library, code generator, or application on top of the API. It answers the
  question *"what can I do?"* without requiring a live solver.
- **The runtime layer** is what most direct API callers interact with — once
  they know which paths and commands exist, they call ``GetState``,
  ``SetState``, ``GetVar``, or ``SetVar`` to read and write live state.

A typical client discovery workflow looks like this:

.. code-block:: python
   :caption: Python

   # 1. Fetch the API schema — no live solver state required
   schema_resp = dm_stub.GetSchema(
       datamodel_se_pb2.GetSchemaRequest(rules="meshing"),
       metadata=metadata,
   )

   # 2. Walk the schema to find the path you need
   root = schema_resp.info
   print("Available commands:", list(root.commands.keys()))
   print("Available singletons:", list(root.singletons.keys()))

   # 3. Call the runtime layer using the path you discovered
   get_resp = dm_stub.GetState(
       datamodel_se_pb2.GetStateRequest(
           rules="meshing",
           path="GlobalSettings/EnableCleanCAD",
       ),
       metadata=metadata,
   )

See :doc:`../user_guide/build_a_client` for a complete step-by-step walkthrough of both
layers for both services.

Who this documentation is for
------------------------------

This documentation is written for two audiences.

**Developers making direct API calls**
   You want to call a specific RPC — read a setting, execute a command, stream
   field data. Go directly to the runtime sections of the relevant service page:

   - :doc:`../api/services/health` — check server readiness before any other call
   - :doc:`../api/services/connection` — session management and version negotiation
   - :doc:`../api/services/app_utilities` — version, process info, journal, beta flags, exit
   - :doc:`../api/services/datamodel_se` — object-model state read/write, commands, events
   - :doc:`../api/services/settings` — solver configuration read/write, named objects
   - :doc:`../api/services/events` — solver lifecycle events and pause callbacks
   - :doc:`../api/services/field_data` — mesh geometry and field value streaming
   - :doc:`../api/services/monitor` — live residual and report monitor data
   - :doc:`../api/services/reduction` — surface and zone scalar reductions (area, force, etc.)
   - :doc:`../api/services/svar` — per-zone solution variable arrays
   - :doc:`../api/services/transcript` — Fluent console output stream

**Developers building client libraries or applications**
   You are generating code, building a higher-level abstraction, or need to
   enumerate everything the API exposes. Read :doc:`../user_guide/build_a_client` first,
   paying particular attention to the API schema discovery steps. Then read
   :doc:`../user_guide/building_on_the_api` for schema-driven code generation, dynamic
   clients, and the difference in runtime discoverability between the two
   schema-bearing services.

Connection and authentication
------------------------------

All examples in this documentation share the same connection assumptions:

.. include:: ../shared_example_assumptions.rst

Every RPC must be accompanied by a ``metadata`` list containing the server
password:

.. code-block:: python
   :caption: Python

   import grpc

   HOST = "127.0.0.1"   # Fluent server host
   PORT = 50051          # Fluent server port
   PASSWORD = "your-server-password"

   channel = grpc.insecure_channel(f"{HOST}:{PORT}")
   metadata = [("password", PASSWORD)]

Pass ``channel`` and ``metadata`` to every stub you create. The channel
should remain open for the lifetime of your client session.

.. tip::

   Always call the Health service ``Check`` RPC immediately after opening a
   channel to confirm the server is ready before issuing any other calls.
   See :doc:`../api/services/health` for details.
