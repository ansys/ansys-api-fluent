Session setup — connection, health, and application runtime
============================================================

Python client examples for the ``Connection``, ``Health``, and
``ApplicationRuntime`` gRPC services.

For message and field references see :doc:`../../api/services/connection`,
:doc:`../../api/services/health`, and :doc:`../../api/services/app_utilities`.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import (
       connection_pb2, connection_pb2_grpc,
       health_pb2, health_pb2_grpc,
       app_utilities_pb2, app_utilities_pb2_grpc,
   )

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   conn_stub   = connection_pb2_grpc.ConnectionStub(channel)
   health_stub = health_pb2_grpc.HealthStub(channel)
   app_stub    = app_utilities_pb2_grpc.ApplicationRuntimeStub(channel)

.. note::

   Calling ``Connection.Connect`` is optional for most deployments. Passing
   ``metadata=[("password", "...")]`` on each RPC call is sufficient. Use
   ``Connection`` only when your deployment requires explicit version
   negotiation or session lifecycle control.

Checking server health
-----------------------

``Health.Check`` returns the serving status; assert ``SERVING_STATUS_SERVING``
before sending any other RPCs.

.. code-block:: python
   :caption: Python

   # Check with an empty service name — covers the server as a whole.
   resp = health_stub.Check(
       health_pb2.HealthCheckRequest(service=""),
       metadata=metadata,
   )
   print(resp.status)  # -> HealthCheckResponse.SERVING_STATUS_SERVING

   # Check by fully-qualified service name.
   resp = health_stub.Check(
       health_pb2.HealthCheckRequest(
           service="ansys.api.fluent.v1.health.Health"
       ),
       metadata=metadata,
   )
   print(resp.status in {
       health_pb2.HealthCheckResponse.SERVING_STATUS_SERVING,
       health_pb2.HealthCheckResponse.SERVING_STATUS_NOT_SERVING,
       health_pb2.HealthCheckResponse.SERVING_STATUS_SERVICE_UNKNOWN,
       health_pb2.HealthCheckResponse.SERVING_STATUS_UNSPECIFIED,
   })  # -> True

   # Repeated calls must all return the same status.
   statuses = [
       health_stub.Check(health_pb2.HealthCheckRequest(), metadata=metadata).status
       for _ in range(3)
   ]
   print(len(set(statuses)) == 1)  # -> True

Connecting with version negotiation
-------------------------------------

``Connection.Connect`` opens a server-streaming call; read the first response
to confirm the server accepted the version and password.

.. code-block:: python
   :caption: Python

   stream = conn_stub.Connect(
       connection_pb2.ConnectRequest(
           request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
           password="your-server-password",
           version="27.1.0",
       ),
       metadata=metadata,
   )
   print(stream is not None)  # -> True

   first = next(iter(stream))
   stream.cancel()
   print(hasattr(first, "error_code"))  # -> True
   print(first.error_code)              # -> CONNECTION_ERROR_NONE

   # Connecting without specifying a version is also accepted.
   stream = conn_stub.Connect(
       connection_pb2.ConnectRequest(
           request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
           password="your-server-password",
       ),
       metadata=metadata,
   )
   first = next(iter(stream))
   stream.cancel()
   print(first.error_code in {
       connection_pb2.CONNECTION_ERROR_NONE,
       connection_pb2.CONNECTION_ERROR_UNSPECIFIED,
       connection_pb2.CONNECTION_ERROR_VERSION_MISMATCH,
   })  # -> True

Reading the product version
-----------------------------

``GetProductVersion`` returns the major, minor, and patch numbers of the
running Fluent build.

.. code-block:: python
   :caption: Python

   ver = app_stub.GetProductVersion(
       app_utilities_pb2.GetProductVersionRequest(),
       metadata=metadata,
   )
   print(ver.major)  # -> 27
   print(ver.minor)  # -> 1
   print(ver.patch)  # -> 0  (or higher for a patched build)

Reading build information
--------------------------

``GetBuildInfo`` returns the build timestamp, numeric build ID, VCS revision,
and branch of the running binary.

.. code-block:: python
   :caption: Python

   info = app_stub.GetBuildInfo(
       app_utilities_pb2.GetBuildInfoRequest(),
       metadata=metadata,
   )
   print(len(info.build_time) > 0)     # -> True  (e.g. '2025-01-15T10:30:00')
   print(info.build_id > 0)            # -> True
   print(len(info.vcs_revision) > 0)   # -> True  (e.g. 'abc123def')
   print(len(info.vcs_branch) > 0)     # -> True  (e.g. 'main')

Reading process information
-----------------------------

``GetControllerProcessInfo`` and ``GetSolverProcessInfo`` return hostname,
PID, and working directory of the respective Fluent processes.

.. code-block:: python
   :caption: Python

   ctrl = app_stub.GetControllerProcessInfo(
       app_utilities_pb2.GetControllerProcessInfoRequest(),
       metadata=metadata,
   )
   print(ctrl.hostname)           # -> 'compute-node-01'
   print(ctrl.process_id)         # -> 12345  (an integer PID)
   print(ctrl.working_directory)  # -> '/scratch/my_project'

   solver = app_stub.GetSolverProcessInfo(
       app_utilities_pb2.GetSolverProcessInfoRequest(),
       metadata=metadata,
   )
   print(solver.process_id > 0)        # -> True
   print(len(solver.hostname) > 0)     # -> True

Reading the application mode
------------------------------

``GetAppMode`` identifies whether Fluent is running as a meshing session,
solver session, or a specialised variant.

.. code-block:: python
   :caption: Python

   mode_resp = app_stub.GetAppMode(
       app_utilities_pb2.GetAppModeRequest(),
       metadata=metadata,
   )
   print(mode_resp.app_mode)  # -> APP_MODE_SOLVER  (or APP_MODE_MESHING, etc.)

   valid_modes = {
       app_utilities_pb2.APP_MODE_UNSPECIFIED,
       app_utilities_pb2.APP_MODE_MESHING,
       app_utilities_pb2.APP_MODE_SOLVER,
       app_utilities_pb2.APP_MODE_SOLVER_ICING,
       app_utilities_pb2.APP_MODE_SOLVER_AERO,
   }
   print(mode_resp.app_mode in valid_modes)  # -> True

Enabling beta features
-----------------------

``IsBetaEnabled`` queries the current state; ``EnableBeta`` activates beta
features for the session â€” the change persists until the server restarts.

.. code-block:: python
   :caption: Python

   resp = app_stub.IsBetaEnabled(
       app_utilities_pb2.IsBetaEnabledRequest(),
       metadata=metadata,
   )
   print(isinstance(resp.is_beta_enabled, bool))  # -> True

   app_stub.EnableBeta(
       app_utilities_pb2.EnableBetaRequest(),
       metadata=metadata,
   )

   resp = app_stub.IsBetaEnabled(
       app_utilities_pb2.IsBetaEnabledRequest(),
       metadata=metadata,
   )
   print(resp.is_beta_enabled)  # -> True

Recording a Python journal
---------------------------

``StartPythonJournal`` begins recording all Fluent API calls; ``StopPythonJournal``
ends recording and returns the journal as a string (when no file name was given).

.. code-block:: python
   :caption: Python

   # Start an in-memory journal (no file name).
   start_resp = app_stub.StartPythonJournal(
       app_utilities_pb2.StartPythonJournalRequest(),
       metadata=metadata,
   )

   # --- perform simulation work here ---

   # Stop and retrieve the recorded journal string.
   stop_resp = app_stub.StopPythonJournal(
       app_utilities_pb2.StopPythonJournalRequest(
           journal_id=(
               start_resp.journal_id
               if start_resp.HasField("journal_id")
               else None
           )
       ),
       metadata=metadata,
   )
   print(isinstance(stop_resp.journal_str, str))  # -> True

For the complete message and field reference see
:doc:`../../api/services/connection`, :doc:`../../api/services/health`, and
:doc:`../../api/services/app_utilities`.
