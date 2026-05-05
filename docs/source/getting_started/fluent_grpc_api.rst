The Fluent gRPC API
===================

This page gives you a high-level map of the Fluent gRPC API before you explore
any specific service. Familiarity with this overview will make the rest of the
documentation easier to navigate.

What this API gives you
-----------------------

The Fluent gRPC API lets you talk to a running Fluent server from any
programming language that supports gRPC. It is organised as a set of
*services*, each responsible for a specific area of Fluent's functionality.

Two of these services — the **DataModel service** and the **Settings service**
— are the most commonly used and share a similar design. Understanding how they
relate to each other, and what each one covers, is the best starting point.

DataModel service and Settings service
---------------------------------------

These two services offer the same kinds of operations: you can read state,
write state, execute commands, and query the structure of the API itself.
What differs is *which part of Fluent* each service connects you to.

**DataModel service**
   Connects you to Fluent's object-model based applications. You choose which
   application to work with by supplying a *rules* string when making a call.
   Examples of supported applications include:

   - ``"meshing"`` — the meshing workflow
   - ``"workflow"`` — the guided workflow engine
   - ``"preferences"`` — user preferences

   Each application exposes its own tree of objects, parameters, and commands,
   all addressed by a slash-separated path.

**Settings service**
   Connects you to the Fluent solver — boundary conditions, solver controls,
   material properties, and results settings. It uses the same slash-separated
   path style, but the tree it exposes is the solver configuration hierarchy.

.. note::

   The DataModel service also accepts ``"flserver"`` as a rules string, which
   gives access to solver state. However, for all solver-related work the
   **Settings service is strongly preferred** — it provides a cleaner,
   more complete interface to the same data.

Both services expose two complementary layers, described below.

Two layers: schema and runtime
-------------------------------

Both the DataModel service and the Settings service are structured in two
layers that serve different purposes.

**Schema layer**
   Before reading or writing any live data, you can ask the service to describe
   itself: what objects exist, what parameters they have, what commands are
   available, and what types everything uses. This description — called the
   *schema* — is static. It does not depend on a running simulation or any
   particular solver state. It is the contract the service makes with you.

   This layer is most useful when you are building a client library, generating
   code, or exploring an unfamiliar part of the API for the first time.

**Runtime layer**
   Once you know the paths and commands you need, you use the runtime layer to
   read and write live simulation state, and to execute commands against a
   running Fluent session. These calls interact directly with the solver or the
   meshing application that is currently running.

   This is what most direct API callers spend most of their time with.

A typical workflow is: consult the schema once to understand the structure, then
make runtime calls as required.

Other services
--------------

Beyond the DataModel and Settings services, the API includes several
single-purpose services. These do not have a schema layer — they each do
one specific thing:

- **Health** — check whether the Fluent server is ready to accept calls
- **Connection** — session management and version negotiation
- **ApplicationRuntime** — version information, process control, journalling, and exit
- **Events** — subscribe to solver lifecycle events and pause callbacks
- **FieldData** — stream mesh geometry and field values
- **Monitor** — receive live residual and report monitor data
- **Reduction** — compute surface and zone scalar reductions (area, forces, etc.)
- **SolutionVariable** — access per-zone solution variable arrays
- **Transcript** — stream Fluent console output

Who this documentation is for
------------------------------

**Developers making direct API calls**
   You want to call a specific RPC to read a setting, execute a command, or
   stream data. Go directly to the relevant service page in the
   :doc:`../api/services/index` section. A good starting point is always the
   Health service — confirm the server is ready before making any other call.

**Developers building client libraries or applications**
   You are generating code, building a higher-level abstraction, or need to
   enumerate everything the API exposes. Start by reading
   :doc:`../user_guide/build_a_client`, which walks through schema discovery
   and runtime calls for both the DataModel and Settings services.

Connection and authentication
------------------------------

All examples in this documentation share the same connection assumptions:

.. include:: ../shared_example_assumptions.rst

Every call to the API must include the server password as part of the request
metadata. See :doc:`../user_guide/build_a_client` for the standard connection
setup used throughout this documentation.

.. tip::

   Always call the Health service ``Check`` RPC immediately after opening a
   connection to confirm the server is ready before issuing any other calls.
   See :doc:`../api/services/health` for details.
