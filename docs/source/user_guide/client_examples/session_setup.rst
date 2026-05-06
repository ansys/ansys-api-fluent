Session setup — connection, health, and application runtime
=============================================================

This page walks through the full session setup sequence in Python: establishing
a connection, verifying server health, and interacting with the running process.
For message and field references see :doc:`../../api/services/connection`,
:doc:`../../api/services/health`, and :doc:`../../api/services/app_utilities`.

.. include:: ../../shared_example_assumptions.rst

.. note::

   Calling ``Connection.Connect`` is optional for most deployments. Passing
   ``metadata=[("password", "...")]`` on each RPC call is sufficient. Use
   ``Connection`` only when your deployment requires explicit version
   negotiation or pause/resume session lifecycle control.

End-to-end example
-------------------

The example below covers the full start-up sequence: connect with version
negotiation, confirm server health, inspect the running process, optionally
enable beta features, set a working directory, record a journal, and exit.

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

   # --- Step 1: Connect with version negotiation ---
   conn_stub = connection_pb2_grpc.ConnectionStub(channel)
   responses = conn_stub.Connect(
       connection_pb2.ConnectRequest(
           request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
           password="your-server-password",
           version="27.1.0",
       )
   )
   first = next(responses)
   if first.error_code == connection_pb2.CONNECTION_ERROR_PASSWORD_MISMATCH:
       raise RuntimeError("Authentication failed: incorrect password")
   if first.error_code == connection_pb2.CONNECTION_ERROR_VERSION_MISMATCH:
       raise RuntimeError("Version mismatch between client and server")
   if first.error_code != connection_pb2.CONNECTION_ERROR_NONE:
       raise RuntimeError(f"Connection error: {first.error_code}")
   print("Connection accepted")

   # --- Step 2: Verify the server is healthy and ready ---
   health_stub = health_pb2_grpc.HealthStub(channel)
   resp = health_stub.Check(
       health_pb2.HealthCheckRequest(service=""),
       metadata=metadata,
   )
   if resp.status != health_pb2.HealthCheckResponse.SERVING_STATUS_SERVING:
       raise RuntimeError(f"Server not ready (status {resp.status})")
   print("Server is ready")

   # --- Step 3: Inspect the server and configure the session ---
   app_stub = app_utilities_pb2_grpc.ApplicationRuntimeStub(channel)

   # Log the server version.
   ver = app_stub.GetProductVersion(
       app_utilities_pb2.GetProductVersionRequest(), metadata=metadata,
   )
   print(f"Fluent {ver.major}.{ver.minor}.{ver.patch}")

   # Check the application mode (meshing, solver, etc.).
   mode = app_stub.GetAppMode(
       app_utilities_pb2.GetAppModeRequest(), metadata=metadata,
   )
   print("App mode:", mode.app_mode)

   # Enable beta features if not already active.
   if not app_stub.IsBetaEnabled(
       app_utilities_pb2.IsBetaEnabledRequest(), metadata=metadata,
   ).is_beta_enabled:
       app_stub.EnableBeta(app_utilities_pb2.EnableBetaRequest(), metadata=metadata)
       print("Beta features enabled")

   # Point Fluent at the project directory.
   app_stub.SetWorkingDirectory(
       app_utilities_pb2.SetWorkingDirectoryRequest(path="/scratch/my_project"),
       metadata=metadata,
   )

   # Start recording a Python journal of everything that follows.
   app_stub.StartPythonJournal(
       app_utilities_pb2.StartPythonJournalRequest(
           journal_name="/scratch/my_project/session.py"
       ),
       metadata=metadata,
   )

   # --- perform your simulation work here ---

   # Stop journaling and exit cleanly.
   app_stub.StopPythonJournal(
       app_utilities_pb2.StopPythonJournalRequest(), metadata=metadata,
   )
   app_stub.Exit(app_utilities_pb2.ExitRequest(), metadata=metadata)
   channel.close()
