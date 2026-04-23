Field data
==========

The Field Data service provides access to simulation field data including surfaces, scalar fields, vector fields, and spatial information.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``FieldData`` service allows you to:

- Discover available surfaces and mesh information
- Query available scalar and vector fields
- Stream field values (double, float, int, long formats)
- Retrieve mesh node and element data
- Access specialized field data like pathlines and particle tracks

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.field_data``

**Main Classes:**

- ``FieldDataStub``: Client stub for all field data operations
- Request messages: ``GetFieldsRequest``, ``GetSurfacesInfoRequest``, ``GetRangeRequest``, etc.
- Response messages: Corresponding response types
- Payload types: ``DoublePayload``, ``FloatPayload``, ``IntPayload``, ``LongPayload``

Core RPC operations
~~~~~~~~~~~~~~~~~~~

Get surfaces information
------------------------

Retrieve information about available surfaces in the simulation.

.. code-block:: python

   response = field_stub.GetSurfacesInfo(
       field_data_pb2.GetSurfacesInfoRequest(),
       metadata=metadata,
   )
   
   for surface_info in response.surface_info:
       print(f"Surface: {surface_info.surface_name}")
       for surface_id in surface_info.surface_ids:
           print(f"  ID: {surface_id.id}")

Get fields information
----------------------

Discover available scalar fields that can be requested.

.. code-block:: python

   response = field_stub.GetFieldsInfo(
       field_data_pb2.GetFieldsInfoRequest(),
       metadata=metadata,
   )
   
   for field in response.field_info:
       print(f"{field.solver_name}: {field.display_name}")
       print(f"  Section: {field.section}, Domain: {field.domain}")

Get range
---------

Get the minimum and maximum values of a field on a surface.

.. code-block:: python

   request = field_data_pb2.GetRangeRequest(
       field_name="temperature",
       surface_ids=[field_data_pb2.SurfaceId(id=2)],
       node_value=True
   )
   
   response = field_stub.GetRange(
       request,
       metadata=metadata,
   )
   
   print(f"Range: {response.minimum} to {response.maximum}")

Get fields (stream)
-------------------

Stream scalar field values. This is the main way to retrieve field data.

.. code-block:: python

   request = field_data_pb2.GetFieldsRequest(
       provide_bytes_stream=False,
       chunk_size=256 * 1024,
       scalar_field_requests=[
           field_data_pb2.ScalarFieldRequest(
               surface_id=2,
               scalar_field_name="temperature",
               data_location=field_data_pb2.DataLocation.DATA_LOCATION_NODES,
               provide_boundary_values=False
           )
       ]
   )
   
   value_count = 0
   values_min = None
   values_max = None
   
   for chunk in field_stub.GetFields(
       request,
       metadata=metadata,
   ):
       chunk_type = chunk.WhichOneof("chunk")
       
       if chunk_type == "payload_info":
           # Contains metadata about the payload
           continue
       elif chunk_type == "double_payload":
           values = list(chunk.double_payload.payloads)
       elif chunk_type == "float_payload":
           values = [float(v) for v in chunk.float_payload.payloads]
       elif chunk_type == "int_payload":
           values = [float(v) for v in chunk.int_payload.payloads]
       elif chunk_type == "long_payload":
           values = [float(v) for v in chunk.long_payload.payloads]
       else:
           continue
       
       if values:
           value_count += len(values)
           chunk_min = min(values)
           chunk_max = max(values)
           values_min = chunk_min if values_min is None else min(values_min, chunk_min)
           values_max = chunk_max if values_max is None else max(values_max, chunk_max)
   
   print(f"Streamed {value_count} values, range: {values_min} to {values_max}")

Complete example
~~~~~~~~~~~~~~~~

A complete workflow that discovers and streams field data:

.. code-block:: python

   import grpc
   from ansys.api.fluent.v1 import field_data_pb2, field_data_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   def list_field_data():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]
       stub = field_data_pb2_grpc.FieldDataStub(channel)
       
       try:
           # Step 1: Get available surfaces
           print("=== Available Surfaces ===")
           surf_response = stub.GetSurfacesInfo(
               field_data_pb2.GetSurfacesInfoRequest(),
               metadata=metadata,
           )
           
           surface_ids = {}
           for surface_info in surf_response.surface_info:
               for sid in surface_info.surface_ids:
                   surface_ids[sid.id] = surface_info.surface_name
                   print(f"ID {sid.id}: {surface_info.surface_name}")
           
           if not surface_ids:
               print("No surfaces available")
               return
           
           first_surface_id = list(surface_ids.keys())[0]
           
           # Step 2: Get available scalar fields
           print("\n=== Available Scalar Fields ===")
           field_response = stub.GetFieldsInfo(
               field_data_pb2.GetFieldsInfoRequest(),
               metadata=metadata,
           )
           
           if not field_response.field_info:
               print("No scalar fields available")
               return
           
           first_field = field_response.field_info[0].solver_name
           for field_info in field_response.field_info[:5]:
               print(f"{field_info.solver_name}: {field_info.display_name}")
           
           # Step 3: Get field range
           print(f"\n=== Field Range for {first_field} ===")
           range_request = field_data_pb2.GetRangeRequest(
               field_name=first_field,
               surface_ids=[field_data_pb2.SurfaceId(id=first_surface_id)],
               node_value=True
           )
           
           range_response = stub.GetRange(
               range_request,
               metadata=metadata,
           )
           
           print(f"Min: {range_response.minimum:.6g}")
           print(f"Max: {range_response.maximum:.6g}")
           
           # Step 4: Stream field values
           print(f"\n=== Streaming {first_field} data ===")
           stream_request = field_data_pb2.GetFieldsRequest(
               provide_bytes_stream=False,
               chunk_size=256 * 1024,
               scalar_field_requests=[
                   field_data_pb2.ScalarFieldRequest(
                       surface_id=first_surface_id,
                       scalar_field_name=first_field,
                       data_location=field_data_pb2.DataLocation.DATA_LOCATION_NODES,
                       provide_boundary_values=False
                   )
               ]
           )
           
           value_count = 0
           chunk_count = 0
           
           for chunk in stub.GetFields(
               stream_request,
               metadata=metadata,
           ):
               chunk_type = chunk.WhichOneof("chunk")
               
               if chunk_type == "payload_info":
                   chunk_count += 1
               elif chunk_type == "double_payload":
                   value_count += len(chunk.double_payload.payloads)
               elif chunk_type in ["float_payload", "int_payload", "long_payload"]:
                   value_count += len(getattr(chunk, chunk_type).payloads)
           
           print(f"Received {chunk_count} payload chunks with {value_count} values")
           
       except grpc.RpcError as err:
           print(f"Error: {err.code()} - {err.details()}")
           raise
       finally:
           channel.close()

   if __name__ == "__main__":
       list_field_data()

Data location options
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Option
     - Value
     - Description
   * - DATA_LOCATION_NODES
     - Values at mesh nodes
     - Cell vertex values
   * - DATA_LOCATION_ELEMENTS
     - Values at cell centers
     - Averaged to cell centers

Payload types
~~~~~~~~~~~~~

Field data is returned in different numeric formats:

.. list-table::
   :header-rows: 1

   * - Type
     - Python Type
     - Use Case
   * - DoublePayload
     - ``double``
     - High precision values
   * - FloatPayload
     - ``float``
     - Standard precision
   * - IntPayload
     - ``sint32``
     - Integer values
   * - LongPayload
     - ``sint64``
     - Large integer values

Best practices
~~~~~~~~~~~~~~

1. **Always discover first** - Call ``GetSurfacesInfo`` and ``GetFieldsInfo`` before requests
2. **Check field range** - Use ``GetRange`` to understand data before streaming
3. **Use appropriate chunk size** - Larger chunks (256-512 KB) for faster streaming
4. **Handle large streams** - Process chunks incrementally, don't load all in memory

See also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`health` - Health service for connectivity checks
