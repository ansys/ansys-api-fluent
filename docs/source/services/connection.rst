Connection
==========

The Connection service manages client connections to Fluent servers.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``Connection`` service establishes and maintains a bidirectional session between a client and the Fluent server.
It provides:

- Secure connection establishment with authentication
- Version negotiation and compatibility checking
- Connection status monitoring via streamed responses
- Connection lifecycle management (connect, pause, reconnect)
- Error handling for authentication and connection failures

The Connection service is typically the first service you interact with when connecting to a Fluent server.
It must be successfully established before accessing other services like Health or Field Data.

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.connection``

**Main Classes:**

- ``ConnectionStub``: Client stub for connection operations
- ``ConnectRequest``: Request message containing connection parameters
- ``ConnectResponse``: Response message with connection status and error codes
- ``ConnectionError``: Enum defining error conditions

Key message types
~~~~~~~~~~~~~~~~~

**ConnectRequest**

.. list-table::
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - request_type
     - RequestType
     - Type of operation: REQUEST_TYPE_CONNECT or REQUEST_TYPE_PAUSE
   * - password
     - string
     - Authentication password (optional if server doesn't require it)
   * - version
     - string
     - Client version string for compatibility checking

**ConnectionError Enum**

.. list-table::
   :header-rows: 1

   * - Error Code
     - Value
     - Description
   * - CONNECTION_ERROR_UNSPECIFIED
     - 0
     - Default/unspecified state
   * - CONNECTION_ERROR_NONE
     - 1
     - No error; connection successful
   * - CONNECTION_ERROR_PASSWORD_MISMATCH
     - 2
     - Supplied password is incorrect
   * - CONNECTION_ERROR_MAX_CONNECTIONS_COUNT_EXCEEDED
     - 3
     - Maximum concurrent connections exceeded
   * - CONNECTION_ERROR_UNKNOWN
     - 4
     - Unknown or unclassified error
   * - CONNECTION_ERROR_VERSION_MISMATCH
     - 5
     - Client/server versions incompatible
   * - CONNECTION_ERROR_WAIT_TIME_EXPIRED
     - 6
     - Server wait time expired before completion

RPC operations
~~~~~~~~~~~~~~

Connect (server-streaming)
--------------------------

Establishes a connection by sending one ``ConnectRequest`` and receiving a
stream of ``ConnectResponse`` messages. The first response indicates whether
the connection succeeded. The stream may continue to carry status updates for
the lifetime of the session. This RPC must complete successfully before using
other services.

**Basic Parameters:**

.. code-block:: python

   request = connection_pb2.ConnectRequest(
       request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
       password="your-password",
       version="1.0.0"
   )

Individual examples
~~~~~~~~~~~~~~~~~~~

Basic connection
----------------

Establish a connection without authentication:

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import connection_pb2, connection_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051

   channel = grpc.insecure_channel(f"{HOST}:{PORT}")
   stub = connection_pb2_grpc.ConnectionStub(channel)

   # Create a connection request
   request = connection_pb2.ConnectRequest(
       request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
       version="27.1.0"
   )

   # Send connect request
   try:
       responses = stub.Connect(request)
       
       for response in responses:
           if response.error_code == connection_pb2.CONNECTION_ERROR_NONE:
               print("Connected successfully!")
               break
           else:
               print(f"Connection error: {response.error_code}")
               break
   finally:
       channel.close()

Authenticated connection
------------------------

Connect with a password-protected server:

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import connection_pb2, connection_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "secure-password"

   channel = grpc.insecure_channel(f"{HOST}:{PORT}")
   stub = connection_pb2_grpc.ConnectionStub(channel)

   request = connection_pb2.ConnectRequest(
       request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
       password=PASSWORD,
       version="27.1.0"
   )

   try:
       responses = stub.Connect(request)
       
       for response in responses:
           if response.error_code == connection_pb2.CONNECTION_ERROR_NONE:
               print("Authenticated connection established!")
           elif response.error_code == connection_pb2.CONNECTION_ERROR_PASSWORD_MISMATCH:
               print("ERROR: Incorrect password")
           break
   finally:
       channel.close()

Connection with error handling
------------------------------

Handle various connection error scenarios:

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import connection_pb2, connection_pb2_grpc

   def connect_with_error_handling(host, port, password=None):
       channel = grpc.insecure_channel(f"{host}:{port}")
       stub = connection_pb2_grpc.ConnectionStub(channel)

       error_messages = {
           connection_pb2.CONNECTION_ERROR_NONE: "No error",
           connection_pb2.CONNECTION_ERROR_PASSWORD_MISMATCH: "Incorrect password",
           connection_pb2.CONNECTION_ERROR_MAX_CONNECTIONS_COUNT_EXCEEDED: 
               "Server connection limit reached",
           connection_pb2.CONNECTION_ERROR_UNKNOWN: "Unknown error",
           connection_pb2.CONNECTION_ERROR_VERSION_MISMATCH: "Version mismatch",
           connection_pb2.CONNECTION_ERROR_WAIT_TIME_EXPIRED: "Connection timeout"
       }

       request = connection_pb2.ConnectRequest(
           request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
           password=password or "",
           version="27.1.0"
       )

       try:
           responses = stub.Connect(request)
           
           for response in responses:
               error_msg = error_messages.get(
                   response.error_code, 
                   f"Unknown error code {response.error_code}"
               )
               
               if response.error_code == connection_pb2.CONNECTION_ERROR_NONE:
                   print(f"✓ Connection successful: {error_msg}")
                   return True, channel, stub
               else:
                   print(f"✗ Connection failed: {error_msg}")
                   return False, None, None
                   
       except grpc.RpcError as err:
           print(f"RPC error: {err.details()}")
           return False, None, None

Complete end-to-end example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A comprehensive workflow connecting to a Fluent server and performing operations across multiple services:

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import (
       connection_pb2, 
       connection_pb2_grpc,
       health_pb2,
       health_pb2_grpc,
       field_data_pb2,
       field_data_pb2_grpc
   )

   class FluentClient:
       """Client for interacting with Fluent server"""
       
       def __init__(self, host="127.0.0.1", port=50051, password=None):
           self.host = host
           self.port = port
           self.password = password or ""
           self.channel = None
           self.connection_stub = None
           self.health_stub = None
           self.field_data_stub = None
           self.response_stream = None

       def connect(self):
           """Establish connection to Fluent server"""
           print(f"Connecting to {self.host}:{self.port}...")
           
           self.channel = grpc.insecure_channel(f"{self.host}:{self.port}")
           self.connection_stub = connection_pb2_grpc.ConnectionStub(self.channel)
           
           connect_request = connection_pb2.ConnectRequest(
               request_type=connection_pb2.ConnectRequest.REQUEST_TYPE_CONNECT,
               password=self.password,
               version="1.0.0"
           )
           
           # Create request generator
           def request_gen():
               yield connect_request
           
           try:
               self.response_stream = self.connection_stub.Connect(
                   request_gen()
               )
               
               # Get first response to verify connection
               first_response = next(self.response_stream)
               
               if first_response.error_code == connection_pb2.CONNECTION_ERROR_NONE:
                   print("✓ Connection established successfully")
                   return True
               else:
                   error_name = self._error_code_to_string(first_response.error_code)
                   print(f"✗ Connection failed: {error_name}")
                   return False
                   
           except grpc.RpcError as err:
               print(f"✗ Connection RPC failed: {err.details()}")
               return False

       def check_server_health(self):
           """Verify server is healthy and ready"""
           if not self.channel:
               print("✗ Not connected. Call connect() first.")
               return False
           
           print("Checking server health...")
           
           health_stub = health_pb2_grpc.HealthStub(self.channel)
           
           try:
               response = health_stub.Check(
                   health_pb2.HealthCheckRequest(service="")
               )
               
               if response.status == 1:  # SERVING
                   print("✓ Server is healthy and ready")
                   return True
               else:
                   print("✗ Server is not healthy")
                   return False
                   
           except grpc.RpcError as err:
               print(f"✗ Health check failed: {err.details()}")
               return False

       def get_available_surfaces(self):
           """Retrieve list of available surfaces"""
           if not self.channel:
               print("✗ Not connected. Call connect() first.")
               return []
           
           print("Fetching available surfaces...")
           
           field_data_stub = field_data_pb2_grpc.FieldDataStub(self.channel)
           
           try:
               response = field_data_stub.GetSurfacesInfo(
                   field_data_pb2.GetSurfacesInfoRequest()
               )
               
               surfaces = []
               for surface_info in response.surface_info:
                   for sid in surface_info.surface_ids:
                       surfaces.append({
                           "id": sid.id,
                           "name": surface_info.surface_name
                       })
               
               print(f"✓ Found {len(surfaces)} surfaces")
               for surf in surfaces[:5]:
                   print(f"  - ID: {surf['id']}, Name: {surf['name']}")
               
               return surfaces
               
           except grpc.RpcError as err:
               print(f"✗ Failed to get surfaces: {err.details()}")
               return []

       def disconnect(self):
           """Close connection to server"""
           if self.channel:
               print("Disconnecting...")
               self.channel.close()
               print("✓ Disconnected")

       @staticmethod
       def _error_code_to_string(error_code):
           """Convert error code to human-readable string"""
           error_map = {
               connection_pb2.CONNECTION_ERROR_NONE: "No error",
               connection_pb2.CONNECTION_ERROR_PASSWORD_MISMATCH: "Password mismatch",
               connection_pb2.CONNECTION_ERROR_MAX_CONNECTIONS_COUNT_EXCEEDED: 
                   "Max connections exceeded",
               connection_pb2.CONNECTION_ERROR_UNKNOWN: "Unknown error",
               connection_pb2.CONNECTION_ERROR_VERSION_MISMATCH: "Version mismatch",
               connection_pb2.CONNECTION_ERROR_WAIT_TIME_EXPIRED: "Connection timeout"
           }
           return error_map.get(error_code, f"Unknown error ({error_code})")

   # Usage
   if __name__ == "__main__":
       client = FluentClient(
           host="127.0.0.1",
           port=50051,
           password="your-password"
       )
       
       try:
           # Step 1: Connect to server
           if not client.connect():
               print("Failed to connect to server")
               exit(1)
           
           # Step 2: Verify server health
           if not client.check_server_health():
               print("Server is not ready")
               exit(1)
           
           # Step 3: Get available surfaces
           surfaces = client.get_available_surfaces()
           if surfaces:
               print(f"\nSuccessfully retrieved {len(surfaces)} surfaces")
               print("Ready to stream field data!")
           
       except KeyboardInterrupt:
           print("\nInterrupted by user")
       except Exception as err:
           print(f"Unexpected error: {err}")
       finally:
           client.disconnect()

Best practices
~~~~~~~~~~~~~~

1. **Always establish connection first**: The Connection service must be successfully connected
   before attempting to use other services (Health, Field Data, etc.).

2. **Handle authentication errors**: Always check for CONNECTION_ERROR_PASSWORD_MISMATCH
   and guide users to verify credentials.

3. **Version compatibility**: Include a client version string to allow the server to detect
   and report version mismatches early.

4. **Clean up resources**: Always close the gRPC channel in a finally block to avoid
   resource leaks.

5. **Implement retry logic**: For transient errors, implement exponential backoff retry logic.

6. **Monitor connection status**: In long-running applications, periodically check server
   health to detect connection drops.

See also
--------

- :doc:`../gettingstarted` — basic client setup
- :doc:`health` — check server readiness after connecting
- :doc:`app_utilities` — version and process information once connected
