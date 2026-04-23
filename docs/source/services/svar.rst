Solution variables
==================

The Solution Variables service provides metadata and streaming access to Fluent
solution variables for domains and zones.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The Solution Variables service allows you to:

- Discover available domains and zones
- Discover available solution variables for a specific domain and zone
- Stream solution variable values efficiently in typed chunks
- Upload solution variable values through a client-streaming API

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.svar``

**Main Classes:**

- ``SvarStub``: Client stub for metadata and data operations
- Request messages: ``GetZonesInfoRequest``, ``GetSvarsInfoRequest``,
  ``GetSvarDataRequest``, ``SetSvarDataRequest``
- Response messages: ``GetZonesInfoResponse``, ``GetSvarsInfoResponse``,
  ``GetSvarDataResponse``, ``SetSvarDataResponse``
- Data containers: ``Info``, ``Payload``, ``SvarHeader``

Core RPC operations
~~~~~~~~~~~~~~~~~~~

Get zones information
---------------------

Retrieves domain and zone metadata.

.. code-block:: python

   response = svar_stub.GetZonesInfo(
	   svar_pb2.GetZonesInfoRequest(),
	   metadata=metadata,
	   timeout=10.0,
   )

   for domain in response.domains_info:
	   print(f"Domain {domain.domain_id}: {domain.name}")

   for zone in response.zones_info:
	   print(f"Zone {zone.zone_id}: {zone.name} ({zone.zone_type})")

Get solution variables information
----------------------------------

Retrieves solution variable metadata for a given domain and zone.

.. code-block:: python

   response = svar_stub.GetSvarsInfo(
	   svar_pb2.GetSvarsInfoRequest(domain_id=1, zone_id=12),
	   metadata=metadata,
	   timeout=10.0,
   )

   for variable in response.svars_info:
	   print(
		   f"{variable.name}: dimension={variable.dimension}, field_type={variable.field_type}"
	   )

Get solution variables data (server stream)
-------------------------------------------

Streams solution variable data as:

- ``payload_info`` (field type, field size, zone)
- ``payload`` chunks (float, double, int, long, or byte payload)

.. code-block:: python

   request = svar_pb2.GetSvarDataRequest(
	   provide_bytes_stream=False,
	   chunk_size=256 * 1024,
	   name="SV_P",
	   domain_id=1,
	   zones=[12],
   )

   for msg in svar_stub.GetSvarData(request, metadata=metadata, timeout=120.0):
	   msg_type = msg.WhichOneof("array")
	   if msg_type == "payload_info":
		   info = msg.payload_info
		   print(f"zone={info.zone}, field_type={info.field_type}, size={info.field_size}")
	   elif msg_type == "payload":
		   payload_type = msg.payload.WhichOneof("chunk")
		   print(f"payload chunk type: {payload_type}")

Set solution variable data (client stream)
------------------------------------------

Writes solution variable data with a client-streamed request iterator.

Correct request ordering:

1. Send one ``header`` per write call
2. For each zone, send one ``payload_info``
3. Then send one or more ``payload`` chunks for that zone

.. code-block:: python

   import math
   import numpy as np
   from ansys.api.fluent.v1 import field_data_pb2, svar_pb2


   def payload_for_array(values: np.ndarray):
	   if values.dtype == np.float32:
		   return svar_pb2.Payload(
			   float_payload=field_data_pb2.FloatPayload(payloads=values)
		   )
	   if values.dtype == np.float64:
		   return svar_pb2.Payload(
			   double_payload=field_data_pb2.DoublePayload(payloads=values)
		   )
	   if values.dtype == np.int32:
		   return svar_pb2.Payload(
			   int_payload=field_data_pb2.IntPayload(payloads=values)
		   )
	   if values.dtype == np.int64:
		   return svar_pb2.Payload(
			   long_payload=field_data_pb2.LongPayload(payloads=values)
		   )
	   raise TypeError(f"Unsupported dtype: {values.dtype}")


   def field_type_for_array(values: np.ndarray):
	   if values.dtype == np.float32:
		   return field_data_pb2.FieldType.FLOAT
	   if values.dtype == np.float64:
		   return field_data_pb2.FieldType.DOUBLE
	   if values.dtype == np.int32:
		   return field_data_pb2.FieldType.INT
	   if values.dtype == np.int64:
		   return field_data_pb2.FieldType.LONG
	   raise TypeError(f"Unsupported dtype: {values.dtype}")


   def build_set_stream(name, domain_id, zone_id_to_values, chunk_size=256 * 1024):
	   yield svar_pb2.SetSvarDataRequest(
		   header=svar_pb2.SvarHeader(name=name, domain_id=domain_id)
	   )

	   for zone_id, zone_values in zone_id_to_values.items():
		   values = np.asarray(zone_values)
		   max_values_per_chunk = max(1, chunk_size // values.dtype.itemsize)
		   n_chunks = int(math.ceil(values.size / max_values_per_chunk))
		   chunks = np.array_split(values, n_chunks) if values.size else []

		   yield svar_pb2.SetSvarDataRequest(
			   payload_info=svar_pb2.Info(
				   field_type=field_type_for_array(values),
				   field_size=values.size,
				   zone=zone_id,
			   )
		   )

		   for chunk in chunks:
			   if chunk.size == 0:
				   continue
			   yield svar_pb2.SetSvarDataRequest(payload=payload_for_array(chunk))


   zone_data = {
	   12: np.full(1000, 500.0, dtype=np.float64),
	   34: np.full(2000, 600.0, dtype=np.float64),
   }

   svar_stub.SetSvarData(
	   build_set_stream(name="SV_P", domain_id=1, zone_id_to_values=zone_data),
	   metadata=metadata,
	   timeout=120.0,
   )

Small usage examples
~~~~~~~~~~~~~~~~~~~~

Example 1: find the first cell zone
-----------------------------------

.. code-block:: python

   zones = svar_stub.GetZonesInfo(
	   svar_pb2.GetZonesInfoRequest(),
	   metadata=metadata,
	   timeout=10.0,
   ).zones_info

   first_cell_zone = next(
	   (z for z in zones if z.thread_type == svar_pb2.THREAD_TYPE_CELL),
	   None,
   )
   if first_cell_zone is None:
	   raise RuntimeError("No cell zone available")

   print(first_cell_zone.name, first_cell_zone.zone_id)

Example 2: find a specific variable
-----------------------------------

.. code-block:: python

   info = svar_stub.GetSvarsInfo(
	   svar_pb2.GetSvarsInfoRequest(domain_id=1, zone_id=12),
	   metadata=metadata,
	   timeout=10.0,
   )

   has_pressure = any(v.name == "SV_P" for v in info.svars_info)
   print(f"SV_P available: {has_pressure}")

Example 3: decode payload chunks
--------------------------------

.. code-block:: python

   def payload_to_list(payload):
	   kind = payload.WhichOneof("chunk")
	   if kind == "float_payload":
		   return [float(v) for v in payload.float_payload.payloads]
	   if kind == "double_payload":
		   return [float(v) for v in payload.double_payload.payloads]
	   if kind == "int_payload":
		   return [int(v) for v in payload.int_payload.payloads]
	   if kind == "long_payload":
		   return [int(v) for v in payload.long_payload.payloads]
	   if kind == "byte_payload":
		   return list(payload.byte_payload)
	   return []

End-to-end example script
~~~~~~~~~~~~~~~~~~~~~~~~~

The following script performs a robust read and optional write workflow.

.. code-block:: python

   import math
   import grpc
   import numpy as np
   from ansys.api.fluent.v1 import field_data_pb2, svar_pb2, svar_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"
   CHUNK_SIZE = 256 * 1024
   WRITE_BACK = False


   def dtype_from_field_type(field_type):
	   if field_type == field_data_pb2.FieldType.FLOAT:
		   return np.float32
	   if field_type == field_data_pb2.FieldType.DOUBLE:
		   return np.float64
	   if field_type == field_data_pb2.FieldType.INT:
		   return np.int32
	   if field_type == field_data_pb2.FieldType.LONG:
		   return np.int64
	   raise ValueError(f"Unsupported field type: {field_type}")


   def payload_to_array(payload, dtype):
	   kind = payload.WhichOneof("chunk")
	   if kind == "byte_payload":
		   return np.frombuffer(payload.byte_payload, dtype=dtype)
	   if kind == "float_payload":
		   return np.asarray(payload.float_payload.payloads, dtype=np.float32).astype(dtype, copy=False)
	   if kind == "double_payload":
		   return np.asarray(payload.double_payload.payloads, dtype=np.float64).astype(dtype, copy=False)
	   if kind == "int_payload":
		   return np.asarray(payload.int_payload.payloads, dtype=np.int32).astype(dtype, copy=False)
	   if kind == "long_payload":
		   return np.asarray(payload.long_payload.payloads, dtype=np.int64).astype(dtype, copy=False)
	   raise RuntimeError(f"Unsupported payload kind: {kind}")


   def read_zone_values(stub, metadata, variable_name, domain_id, zone_id):
	   request = svar_pb2.GetSvarDataRequest(
		   provide_bytes_stream=False,
		   chunk_size=CHUNK_SIZE,
		   name=variable_name,
		   domain_id=domain_id,
		   zones=[zone_id],
	   )

	   payload_info = None
	   payloads = []
	   for msg in stub.GetSvarData(request, metadata=metadata, timeout=120.0):
		   part = msg.WhichOneof("array")
		   if part == "payload_info":
			   payload_info = msg.payload_info
		   elif part == "payload":
			   payloads.append(msg.payload)

	   if payload_info is None:
		   raise RuntimeError(f"No payload_info for zone {zone_id}")

	   dtype = dtype_from_field_type(payload_info.field_type)
	   values = np.empty(payload_info.field_size, dtype=dtype)

	   idx = 0
	   for payload in payloads:
		   arr = payload_to_array(payload, dtype)
		   end = min(values.size, idx + arr.size)
		   values[idx:end] = arr[: end - idx]
		   idx = end
		   if idx == values.size:
			   break

	   if idx != values.size:
		   raise RuntimeError(f"Incomplete data: expected {values.size}, received {idx}")

	   return values, payload_info.field_type


   def payload_for_array(values):
	   if values.dtype == np.float32:
		   return svar_pb2.Payload(float_payload=field_data_pb2.FloatPayload(payloads=values))
	   if values.dtype == np.float64:
		   return svar_pb2.Payload(double_payload=field_data_pb2.DoublePayload(payloads=values))
	   if values.dtype == np.int32:
		   return svar_pb2.Payload(int_payload=field_data_pb2.IntPayload(payloads=values))
	   if values.dtype == np.int64:
		   return svar_pb2.Payload(long_payload=field_data_pb2.LongPayload(payloads=values))
	   raise ValueError(f"Unsupported dtype: {values.dtype}")


   def field_type_for_dtype(dtype):
	   if dtype == np.float32:
		   return field_data_pb2.FieldType.FLOAT
	   if dtype == np.float64:
		   return field_data_pb2.FieldType.DOUBLE
	   if dtype == np.int32:
		   return field_data_pb2.FieldType.INT
	   if dtype == np.int64:
		   return field_data_pb2.FieldType.LONG
	   raise ValueError(f"Unsupported dtype: {dtype}")


   def build_set_stream(variable_name, domain_id, zone_id_to_values):
	   yield svar_pb2.SetSvarDataRequest(
		   header=svar_pb2.SvarHeader(name=variable_name, domain_id=domain_id)
	   )

	   for zone_id, zone_values in zone_id_to_values.items():
		   values = np.asarray(zone_values)
		   max_values_per_chunk = max(1, CHUNK_SIZE // values.dtype.itemsize)
		   n_chunks = int(math.ceil(values.size / max_values_per_chunk))
		   chunks = np.array_split(values, n_chunks) if values.size else []

		   yield svar_pb2.SetSvarDataRequest(
			   payload_info=svar_pb2.Info(
				   field_type=field_type_for_dtype(values.dtype.type),
				   field_size=values.size,
				   zone=zone_id,
			   )
		   )

		   for chunk in chunks:
			   if chunk.size > 0:
				   yield svar_pb2.SetSvarDataRequest(payload=payload_for_array(chunk))


   def run_workflow():
	   channel = grpc.insecure_channel(f"{HOST}:{PORT}")
	   metadata = [("password", PASSWORD)]
	   stub = svar_pb2_grpc.SvarStub(channel)

	   try:
		   zones_response = stub.GetZonesInfo(
			   svar_pb2.GetZonesInfoRequest(),
			   metadata=metadata,
			   timeout=10.0,
		   )
		   if not zones_response.domains_info:
			   raise RuntimeError("No domains available")

		   domain_id = zones_response.domains_info[0].domain_id
		   zone_ids = [z.zone_id for z in zones_response.zones_info[:2]]
		   if len(zone_ids) < 2:
			   raise RuntimeError("At least two zones are required for this example")

		   values_a, _ = read_zone_values(stub, metadata, "SV_P", domain_id, zone_ids[0])
		   values_b, _ = read_zone_values(stub, metadata, "SV_P", domain_id, zone_ids[1])
		   print(f"Zone {zone_ids[0]} size={values_a.size} dtype={values_a.dtype}")
		   print(f"Zone {zone_ids[1]} size={values_b.size} dtype={values_b.dtype}")

		   if WRITE_BACK:
			   zone_data = {
				   zone_ids[0]: np.full(values_a.shape, 500.0, dtype=values_a.dtype),
				   zone_ids[1]: np.full(values_b.shape, 600.0, dtype=values_b.dtype),
			   }
			   stub.SetSvarData(
				   build_set_stream("SV_P", domain_id, zone_data),
				   metadata=metadata,
				   timeout=120.0,
			   )
			   print("SetSvarData completed")

	   except grpc.RpcError as err:
		   print(f"Solution Variables error: {err.code()} - {err.details()}")
		   raise
	   finally:
		   channel.close()


   if __name__ == "__main__":
	   run_workflow()

ThreadType values
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Enum
	 - Value
	 - Meaning
   * - ``THREAD_TYPE_UNSPECIFIED``
	 - 0
	 - Unknown or unspecified thread type
   * - ``THREAD_TYPE_CELL``
	 - 1
	 - Zone is represented as a cell thread
   * - ``THREAD_TYPE_FACE``
	 - 2
	 - Zone is represented as a face thread

Best practices
~~~~~~~~~~~~~~

1. **Discover before requesting** - Use ``GetZonesInfo`` and ``GetSvarsInfo`` before ``GetSvarData``.
2. **Use correct stream ordering for writes** - ``header`` once, then for each zone: ``payload_info`` followed by payload chunks.
3. **Chunk by item size** - Compute values per chunk using ``chunk_size // dtype.itemsize``.
4. **Preserve type consistency** - Keep payload type aligned with variable field type.
5. **Validate expected field size** - Ensure reconstructed data length matches ``payload_info.field_size``.
6. **Set practical timeouts** - Large meshes and multi-zone writes can require longer timeouts.

See also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`field_data` - Field data service (payload types and field type enum)
- :doc:`reduction` - Reduction service for scalar and vector post-processing

