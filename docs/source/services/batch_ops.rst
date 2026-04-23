Batch operations
================

The Batch Operations service provides batch execution capabilities for command sequences.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``BatchOps`` service allows you to:

- Execute batch commands
- Chain multiple operations
- Manage batch execution state

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.batch_ops``

**Main Classes:**

- ``BatchOpsStub``: Client stub for batch operations

Core RPC operations
~~~~~~~~~~~~~~~~~~~

Execute
-------

Execute a batch of operations.

.. code-block:: python

   request = batch_ops_pb2.ExecuteRequest(
       # Populate with batch commands
   )
   
   response = batch_stub.Execute(
       request,
       metadata=metadata,
       timeout=30.0
   )

Complete example
~~~~~~~~~~~~~~~~

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import batch_ops_pb2, batch_ops_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   def execute_batch():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = batch_ops_pb2_grpc.BatchOpsStub(channel)
       
       try:
           request = batch_ops_pb2.ExecuteRequest()
           # Add batch commands here
           
           response = stub.Execute(
               request,
               metadata=metadata,
               timeout=30.0
           )
           
           print(f"Batch execution completed")
           
       except grpc.RpcError as err:
           print(f"Error: {err.code()} - {err.details()}")
           raise
       finally:
           channel.close()

   if __name__ == "__main__":
       execute_batch()

See also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
