ApplicationRuntime
==================

Overview
--------

The ``ApplicationRuntime`` service exposes application-level operations that span
the Fluent process lifecycle: retrieving version and build metadata, inspecting
process information in client-server mode, managing Python journal recording,
controlling experimental feature flags, setting the working directory, and
shutting down the application.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import app_utilities_pb2, app_utilities_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = app_utilities_pb2_grpc.ApplicationRuntimeStub(channel)

Runtime API
-----------

Version and build information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieve the version number and build metadata of the running Fluent
installation. Call these immediately after the health check to log which server
version you are connected to.

- ``GetProductVersion(GetProductVersionRequest)`` ? ``GetProductVersionResponse``
  Response fields: ``major: int64``, ``minor: int64``, ``patch: int64``
- ``GetBuildInfo(GetBuildInfoRequest)`` ? ``GetBuildInfoResponse``
  Response fields: ``build_time: string``, ``build_id: int64``, ``vcs_revision: string``, ``vcs_branch: string``

.. code-block:: python
   :caption: Python

   ver = stub.GetProductVersion(
       app_utilities_pb2.GetProductVersionRequest(), metadata=metadata,
   )
   print(f"Fluent {ver.major}.{ver.minor}.{ver.patch}")

   build = stub.GetBuildInfo(
       app_utilities_pb2.GetBuildInfoRequest(), metadata=metadata,
   )
   print(f"Build {build.build_id} on branch {build.vcs_branch} (rev {build.vcs_revision})")
   print(f"Built at: {build.build_time}")

Process information
~~~~~~~~~~~~~~~~~~~

In a Fluent client-server deployment a Controller process commands a separate
Solver process. These two RPCs return the host, process ID, and working
directory of each process so you can correlate logs or connect debuggers.

- ``GetControllerProcessInfo(GetControllerProcessInfoRequest)`` ? ``GetControllerProcessInfoResponse``
  Response fields: ``hostname: string``, ``process_id: int64``, ``working_directory: string``
- ``GetSolverProcessInfo(GetSolverProcessInfoRequest)`` ? ``GetSolverProcessInfoResponse``
  Response fields: ``hostname: string``, ``process_id: int64``, ``working_directory: string``

.. code-block:: python
   :caption: Python

   ctrl = stub.GetControllerProcessInfo(
       app_utilities_pb2.GetControllerProcessInfoRequest(), metadata=metadata,
   )
   print(f"Controller: pid={ctrl.process_id} host={ctrl.hostname} cwd={ctrl.working_directory}")

   solver = stub.GetSolverProcessInfo(
       app_utilities_pb2.GetSolverProcessInfoRequest(), metadata=metadata,
   )
   print(f"Solver:     pid={solver.process_id} host={solver.hostname} cwd={solver.working_directory}")

Application mode
~~~~~~~~~~~~~~~~

Returns the current mode Fluent is operating in — meshing, solver, or a
specialised solver variant. Use this to branch client logic when the same
process can run in multiple modes.

- ``GetAppMode(GetAppModeRequest)`` ? ``GetAppModeResponse``
  Response field: ``app_mode: AppMode``

.. list-table:: ``AppMode`` enum values
   :header-rows: 1
   :widths: 10 30 60

   * - Value
     - Constant
     - Description
   * - 0
     - ``APP_MODE_UNSPECIFIED``
     - Default; do not use.
   * - 1
     - ``APP_MODE_MESHING``
     - Fluent is in meshing mode.
   * - 2
     - ``APP_MODE_SOLVER``
     - Fluent is in solver mode.
   * - 3
     - ``APP_MODE_SOLVER_ICING``
     - Fluent is in icing-solver mode.
   * - 4
     - ``APP_MODE_SOLVER_AERO``
     - Fluent is in aerodynamics-solver mode.

.. code-block:: python
   :caption: Python

   mode_resp = stub.GetAppMode(
       app_utilities_pb2.GetAppModeRequest(), metadata=metadata,
   )

   MODE_LABELS = {
       app_utilities_pb2.APP_MODE_UNSPECIFIED:   "Unspecified",
       app_utilities_pb2.APP_MODE_MESHING:       "Meshing",
       app_utilities_pb2.APP_MODE_SOLVER:        "Solver",
       app_utilities_pb2.APP_MODE_SOLVER_ICING:  "Solver Icing",
       app_utilities_pb2.APP_MODE_SOLVER_AERO:   "Solver Aero",
   }
   print("Mode:", MODE_LABELS.get(mode_resp.app_mode, "Unknown"))

Python journal recording
~~~~~~~~~~~~~~~~~~~~~~~~

Fluent can record all API interactions to a Python journal file so that the
session can be replayed later. Start recording with ``StartPythonJournal`` and
stop it with ``StopPythonJournal``.

If you set ``journal_name``, the journal is written to that file on the server.
If you omit it, the server tracks the journal in memory and returns its content
in ``StopPythonJournalResponse.journal_str``; it also returns a ``journal_id``
in ``StartPythonJournalResponse`` that you must pass to ``StopPythonJournal``.

- ``StartPythonJournal(StartPythonJournalRequest)`` ? ``StartPythonJournalResponse``
  Request field: ``journal_name: optional string``
  Response field: ``journal_id: optional string`` (returned when no file name given)
- ``StopPythonJournal(StopPythonJournalRequest)`` ? ``StopPythonJournalResponse``
  Request field: ``journal_id: optional string``
  Response field: ``journal_str: string`` (journal content when no file name was given)

.. code-block:: python
   :caption: Python

   # Write journal to a file
   stub.StartPythonJournal(
       app_utilities_pb2.StartPythonJournalRequest(
           journal_name="/tmp/my_session.py",
       ),
       metadata=metadata,
   )

   # ... perform API calls that will be journaled ...

   stub.StopPythonJournal(
       app_utilities_pb2.StopPythonJournalRequest(), metadata=metadata,
   )

   # Alternatively, capture journal content in memory (omit journal_name)
   start_resp = stub.StartPythonJournal(
       app_utilities_pb2.StartPythonJournalRequest(),
       metadata=metadata,
   )
   stop_resp = stub.StopPythonJournal(
       app_utilities_pb2.StopPythonJournalRequest(
           journal_id=start_resp.journal_id,
       ),
       metadata=metadata,
   )
   print(stop_resp.journal_str)

Beta features
~~~~~~~~~~~~~

Fluent may ship experimental features that are disabled by default. These two
RPCs let you check whether beta features are active and enable them if needed.
Enabling beta features affects the current session only.

- ``IsBetaEnabled(IsBetaEnabledRequest)`` ? ``IsBetaEnabledResponse``
  Response field: ``is_beta_enabled: bool``
- ``EnableBeta(EnableBetaRequest)`` ? ``EnableBetaResponse``

.. code-block:: python
   :caption: Python

   beta_resp = stub.IsBetaEnabled(
       app_utilities_pb2.IsBetaEnabledRequest(), metadata=metadata,
   )
   if not beta_resp.is_beta_enabled:
       stub.EnableBeta(
           app_utilities_pb2.EnableBetaRequest(), metadata=metadata,
       )
       print("Beta features enabled for this session")

Working directory
~~~~~~~~~~~~~~~~~

Changes the working directory of the Fluent process. Subsequent file operations
that use relative paths will resolve against the new directory.

- ``SetWorkingDirectory(SetWorkingDirectoryRequest)`` ? ``SetWorkingDirectoryResponse``
  Request field: ``path: string``

.. code-block:: python
   :caption: Python

   stub.SetWorkingDirectory(
       app_utilities_pb2.SetWorkingDirectoryRequest(path="/scratch/my_project"),
       metadata=metadata,
   )

Exiting the application
~~~~~~~~~~~~~~~~~~~~~~~

Terminates the Fluent process. Call this only when your session is complete.
The server will close the connection after processing the request; no further
calls on the channel will succeed.

- ``Exit(ExitRequest)`` ? ``ExitResponse``

.. code-block:: python
   :caption: Python

   stub.Exit(app_utilities_pb2.ExitRequest(), metadata=metadata)
   channel.close()

See also
--------

- :doc:`../../getting_started/gettingstarted` — basic client setup
- :doc:`health` — confirm the server is ready before calling ApplicationRuntime RPCs
- :doc:`transcript` — stream Fluent console output alongside journal recording

.. ----------------------------------------------------------------------------
.. The block below is generated by docs/_ext/proto_docgen.py from the matching
.. .proto file in ansys/api/fluent/v1. Edit the proto comments to update it.
.. ----------------------------------------------------------------------------
