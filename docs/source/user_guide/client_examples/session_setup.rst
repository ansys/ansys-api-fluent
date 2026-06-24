Session setup — connection, health, and application runtime
============================================================

Python client examples for the ``Connection``, ``Health``, and
``ApplicationRuntime`` gRPC services.

See :doc:`../../api/services/connection`, :doc:`../../api/services/health`,
and :doc:`../../api/services/application_runtime`
for these services' complete reference material.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import (
       connection_pb2, connection_pb2_grpc,
       health_pb2, health_pb2_grpc,
       application_runtime_pb2, application_runtime_pb2_grpc,
   )

   channel = grpc.insecure_channel("<server-address>")
   metadata = [("password", "<password>")]
   connection_stub = connection_pb2_grpc.ConnectionStub(channel)
   health_stub = health_pb2_grpc.HealthStub(channel)
   application_runtime_stub = application_runtime_pb2_grpc.ApplicationRuntimeStub(channel)

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
   health_response = health_stub.Check(
       health_pb2.HealthCheckRequest(service=""),
       metadata=metadata,
   )
   print(health_response.status)  # -> HealthCheckResponse.SERVING_STATUS_SERVING

   # Check by fully-qualified service name.
   health_response = health_stub.Check(
       health_pb2.HealthCheckRequest(
           service="ansys.api.fluent.v1.health.Health"
       ),
       metadata=metadata,
   )
   print(health_response.status in {
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

   stream = connection_stub.Connect(
       connection_pb2.ConnectRequest(
           request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
           password="your-server-password",
           version="27.1.0",
       ),
       metadata=metadata,
   )
   print(stream is not None)  # -> True

   first_response = next(iter(stream))
   stream.cancel()
   print(hasattr(first_response, "error_code"))  # -> True
   print(first_response.error_code)              # -> CONNECTION_ERROR_NONE

   # Connecting without specifying a version is also accepted.
   stream = connection_stub.Connect(
       connection_pb2.ConnectRequest(
           request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
           password="your-server-password",
       ),
       metadata=metadata,
   )
   first_response = next(iter(stream))
   stream.cancel()
   print(first_response.error_code in {
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

   version_response = application_runtime_stub.GetProductVersion(
       application_runtime_pb2.GetProductVersionRequest(),
       metadata=metadata,
   )
   print(version_response.major)  # -> 27
   print(version_response.minor)  # -> 1
   print(version_response.patch)  # -> 0  (or higher for a patched build)

Reading build information
--------------------------

``GetBuildInfo`` returns the build timestamp, numeric build ID, VCS revision,
and branch of the running binary.

.. code-block:: python
   :caption: Python

   build_info = application_runtime_stub.GetBuildInfo(
       application_runtime_pb2.GetBuildInfoRequest(),
       metadata=metadata,
   )
   print(len(build_info.build_time) > 0)     # -> True  (e.g. '2025-01-15T10:30:00')
   print(build_info.build_id > 0)            # -> True
   print(len(build_info.vcs_revision) > 0)   # -> True  (e.g. 'abc123def')
   print(len(build_info.vcs_branch) > 0)     # -> True  (e.g. 'main')

Reading process information
-----------------------------

``GetControllerProcessInfo`` and ``GetSolverProcessInfo`` return hostname,
PID, and working directory of the respective Fluent processes.

.. code-block:: python
   :caption: Python

   controller_process_info = application_runtime_stub.GetControllerProcessInfo(
       application_runtime_pb2.GetControllerProcessInfoRequest(),
       metadata=metadata,
   )
   print(controller_process_info.hostname)           # -> 'compute-node-01'
   print(controller_process_info.process_id)         # -> 12345  (an integer PID)
   print(controller_process_info.working_directory)  # -> '/scratch/my_project'

   solver_process_info = application_runtime_stub.GetSolverProcessInfo(
       application_runtime_pb2.GetSolverProcessInfoRequest(),
       metadata=metadata,
   )
   print(solver_process_info.process_id > 0)        # -> True
   print(len(solver_process_info.hostname) > 0)     # -> True

Reading the application mode
------------------------------

``GetAppMode`` identifies whether Fluent is running as a meshing session,
solver session, or a specialised variant.

.. code-block:: python
   :caption: Python

   app_mode_response = application_runtime_stub.GetAppMode(
       application_runtime_pb2.GetAppModeRequest(),
       metadata=metadata,
   )
   print(app_mode_response.app_mode)  # -> APP_MODE_SOLVER  (or APP_MODE_MESHING, etc.)

   valid_modes = {
       application_runtime_pb2.APP_MODE_UNSPECIFIED,
       application_runtime_pb2.APP_MODE_MESHING,
       application_runtime_pb2.APP_MODE_SOLVER,
       application_runtime_pb2.APP_MODE_SOLVER_ICING,
       application_runtime_pb2.APP_MODE_SOLVER_AERO,
   }
   print(app_mode_response.app_mode in valid_modes)  # -> True

Enabling beta features
-----------------------

``IsBetaEnabled`` queries the current state; ``EnableBeta`` activates beta
features for the session — the change persists until the server restarts.

.. code-block:: python
   :caption: Python

   beta_status_response = application_runtime_stub.IsBetaEnabled(
       application_runtime_pb2.IsBetaEnabledRequest(),
       metadata=metadata,
   )
   print(isinstance(beta_status_response.is_beta_enabled, bool))  # -> True

   application_runtime_stub.EnableBeta(
       application_runtime_pb2.EnableBetaRequest(),
       metadata=metadata,
   )

   beta_status_response = application_runtime_stub.IsBetaEnabled(
       application_runtime_pb2.IsBetaEnabledRequest(),
       metadata=metadata,
   )
   print(beta_status_response.is_beta_enabled)  # -> True

Recording a Python journal
---------------------------

``StartPythonJournal`` begins recording all Fluent API calls; ``StopPythonJournal``
ends recording and returns the journal as a string (when no file name was given).

.. code-block:: python
   :caption: Python

   # Start an in-memory journal (no file name).
   start_response = application_runtime_stub.StartPythonJournal(
       application_runtime_pb2.StartPythonJournalRequest(),
       metadata=metadata,
   )

   # --- perform simulation work here ---

   # Stop and retrieve the recorded journal string.
   stop_response = application_runtime_stub.StopPythonJournal(
       application_runtime_pb2.StopPythonJournalRequest(
           journal_id=start_response.journal_id
       ),
       metadata=metadata,
   )
   print(isinstance(stop_response.journal_str, str))  # -> True

See :doc:`../../api/services/connection`, :doc:`../../api/services/health`,
and :doc:`../../api/services/application_runtime` for the complete reference material.
