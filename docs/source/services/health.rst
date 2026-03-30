Health Service
==============

The Health service provides RPCs to query the serving status of the server.

Overview
~~~~~~~~

The ``Health`` service is used to verify that your server is running and ready to serve requests. 
Use this as the first check when connecting to a server.

Service Definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.health``

**Main Classes:**

- ``HealthCheckRequest``: Request message (service name)
- ``HealthCheckResponse``: Response with serving status
- ``HealthStub``: Client stub for making requests

RPC Operations
~~~~~~~~~~~~~~

Check
-----

Queries the serving status of a service.

.. code-block:: python

   # Check overall server status
   response = health_stub.Check(
       health_pb2.HealthCheckRequest(),
       metadata=metadata,
       timeout=5.0
   )
   status = response.status
   # Returns: SERVING_STATUS_SERVING (1) if healthy

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   def check_server_health():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = health_pb2_grpc.HealthStub(channel)
       
       try:
           response = stub.Check(
               health_pb2.HealthCheckRequest(service=""),
               metadata=metadata,
               timeout=5.0
           )
           
           status_map = {
               0: "UNSPECIFIED",
               1: "SERVING",
               2: "NOT_SERVING",
               3: "UNKNOWN"
           }
           
           status_name = status_map.get(response.status, "UNKNOWN")
           print(f"Server status: {status_name}")
           
           if response.status == 1:  # SERVING
               return True
           return False
           
       except grpc.RpcError as err:
           print(f"Health check failed: {err.details()}")
           raise
       finally:
           channel.close()

   if __name__ == "__main__":
       is_healthy = check_server_health()
       print(f"Server is {'ready' if is_healthy else 'not ready'}")

Serving Status Values
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Status
     - Value
     - Meaning
   * - UNSPECIFIED
     - 0
     - Default/unspecified status
   * - SERVING
     - 1
     - Server is ready and serving
   * - NOT_SERVING
     - 2
     - Server is not currently serving
   * - UNKNOWN
     - 3
     - Requested service is unknown

Best Practices
~~~~~~~~~~~~~~

1. **Always check health first** - Before using other services, verify the server is healthy
2. **Use reasonable timeouts** - Health checks should be fast (5-10 seconds)
3. **Handle errors gracefully** - Network issues or wrong credentials will raise RpcError
4. **Implement retry logic** - For transient failures, retry with exponential backoff

See Also
~~~~~~~~

- :doc:`gettingstarted` - Basic client setup
- :doc:`field_data` - Field data retrieval service
