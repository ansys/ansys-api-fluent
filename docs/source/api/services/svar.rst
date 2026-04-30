SolutionVariable
================

Overview
--------

The ``SolutionVariable`` service provides metadata discovery and bidirectional
streaming access to per-zone solution variable arrays inside a running Fluent
session. Use it to read raw solver fields (pressure, velocity components, etc.)
at zone level, or to write modified values back into the solver.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import svar_pb2, svar_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = svar_pb2_grpc.SolutionVariableStub(channel)

Runtime API
-----------

Get zones information
~~~~~~~~~~~~~~~~~~~~~

Retrieves the list of domains and zones available in the current session.
Call this first to discover valid ``domain_id`` and ``zone_id`` values to use
in subsequent requests.

- ``GetZonesInfo(GetZonesInfoRequest)`` → ``GetZonesInfoResponse``

``GetZonesInfoResponse`` fields:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Field
     - Type
     - Description
   * - ``domains_info``
     - ``repeated DomainInfo``
     - One entry per domain: ``name`` and ``domain_id``.
   * - ``zones_info``
     - ``repeated ZoneInfo``
     - One entry per zone: ``name``, ``zone_id``, ``zone_type``, ``thread_type``,
       and ``partitions_info``.

.. code-block:: python
   :caption: Python

   zones_resp = stub.GetZonesInfo(
       svar_pb2.GetZonesInfoRequest(),
       metadata=metadata,
   )

   for domain in zones_resp.domains_info:
       print(f"Domain {domain.domain_id}: {domain.name}")

   for zone in zones_resp.zones_info:
       print(f"Zone {zone.zone_id}: {zone.name} ({zone.zone_type})")

``ThreadType`` enum values used in ``ZoneInfo.thread_type``:

.. list-table::
   :header-rows: 1
   :widths: 35 10 55

   * - Constant
     - Value
     - Meaning
   * - ``THREAD_TYPE_UNSPECIFIED``
     - 0
     - Default; do not use.
   * - ``THREAD_TYPE_CELL``
     - 1
     - Zone uses cell threads.
   * - ``THREAD_TYPE_FACE``
     - 2
     - Zone uses face threads.

Get solution variable information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves metadata for the solution variables available on a specific domain
and zone. Use this to confirm that a variable name exists and to learn its
data type and dimension before streaming data.

- ``GetSolutionVariableInfo(GetSolutionVariableInfoRequest)`` → ``GetSolutionVariableInfoResponse``
  Request fields: ``domain_id: uint32``, ``zone_id: uint64``

``GetSolutionVariableInfoResponse`` has one field: ``svars_info`` — a list of
``SolutionVariableInfo`` entries, each containing:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Field
     - Type
     - Description
   * - ``name``
     - ``string``
     - Solution variable name (for example, ``"SV_P"``, ``"SV_U"``).
   * - ``dimension``
     - ``uint32``
     - Number of components per cell (1 for scalars, 3 for vectors like
       centroid).
   * - ``field_type``
     - ``FieldType``
     - Numeric type: ``FLOAT``, ``DOUBLE``, ``INT``, or ``LONG``.

.. code-block:: python
   :caption: Python

   info_resp = stub.GetSolutionVariableInfo(
       svar_pb2.GetSolutionVariableInfoRequest(domain_id=1, zone_id=12),
       metadata=metadata,
   )

   for var in info_resp.svars_info:
       print(f"{var.name}: dimension={var.dimension}, field_type={var.field_type}")

   has_pressure = any(v.name == "SV_P" for v in info_resp.svars_info)
   print(f"SV_P available: {has_pressure}")

Get solution variable data (server stream)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Streams solution variable values for the requested zones as a sequence of
typed payload chunks. Each streamed ``GetSolutionVariableDataResponse``
carries either a ``payload_info`` header (one per zone, sent first) or a
``payload`` data chunk.

- ``GetSolutionVariableData(GetSolutionVariableDataRequest)`` → ``stream GetSolutionVariableDataResponse``

``GetSolutionVariableDataRequest`` fields:

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Field
     - Type
     - Description
   * - ``name``
     - ``string``
     - Solution variable name.
   * - ``domain_id``
     - ``uint32``
     - Domain to read from.
   * - ``zones``
     - ``repeated uint64``
     - Zone IDs to include.
   * - ``chunk_size``
     - ``uint32``
     - Maximum byte size of each payload chunk.
   * - ``provide_bytes_stream``
     - ``bool``
     - If ``True`` the server sends raw ``byte_payload`` chunks instead of
       typed numeric chunks.

``GetSolutionVariableDataResponse`` carries a ``oneof array``:

- ``payload_info`` (``Info``) — sent once per zone; contains ``field_type``,
  ``field_size`` (number of elements), and ``zone`` ID.
- ``payload`` (``Payload``) — one or more data chunks per zone; the ``oneof
  chunk`` inside ``Payload`` is one of ``double_payload``, ``float_payload``,
  ``int_payload``, ``long_payload``, or ``byte_payload``.

.. code-block:: python
   :caption: Python

   request = svar_pb2.GetSolutionVariableDataRequest(
       provide_bytes_stream=False,
       chunk_size=256 * 1024,
       name="SV_P",
       domain_id=1,
       zones=[12],
   )

   payload_info = None
   all_values = []

   for msg in stub.GetSolutionVariableData(request, metadata=metadata):
       part = msg.WhichOneof("array")
       if part == "payload_info":
           payload_info = msg.payload_info
           print(f"zone={payload_info.zone}, size={payload_info.field_size}, "
                 f"type={payload_info.field_type}")
       elif part == "payload":
           chunk_kind = msg.payload.WhichOneof("chunk")
           if chunk_kind == "double_payload":
               all_values.extend(msg.payload.double_payload.payloads)
           elif chunk_kind == "float_payload":
               all_values.extend(msg.payload.float_payload.payloads)

   print(f"Received {len(all_values)} values")

Set solution variable data (client stream)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writes solution variable values back into the solver via a client-streaming
RPC. The client sends a sequence of ``SetSolutionVariableDataRequest``
messages in a strict order:

1. One ``header`` message (``SolutionVariableHeader``) specifying the variable
   name and domain ID.
2. For each zone: one ``payload_info`` (``Info``) message followed by one or
   more ``payload`` (``Payload``) chunk messages.

- ``SetSolutionVariableData(stream SetSolutionVariableDataRequest)`` → ``SetSolutionVariableDataResponse``

``SolutionVariableHeader`` fields: ``name: string``, ``domain_id: uint32``

.. code-block:: python
   :caption: Python

   import math
   import numpy as np
   from ansys.api.fluent.v1 import field_data_pb2

   def _payload_for_array(values: np.ndarray) -> svar_pb2.Payload:
       if values.dtype == np.float32:
           return svar_pb2.Payload(float_payload=field_data_pb2.FloatPayload(payloads=values))
       if values.dtype == np.float64:
           return svar_pb2.Payload(double_payload=field_data_pb2.DoublePayload(payloads=values))
       if values.dtype == np.int32:
           return svar_pb2.Payload(int_payload=field_data_pb2.IntPayload(payloads=values))
       if values.dtype == np.int64:
           return svar_pb2.Payload(long_payload=field_data_pb2.LongPayload(payloads=values))
       raise TypeError(f"Unsupported dtype: {values.dtype}")

   def _field_type_for_array(values: np.ndarray):
       if values.dtype == np.float32:
           return field_data_pb2.FieldType.FIELD_TYPE_FLOAT_ARRAY
       if values.dtype == np.float64:
           return field_data_pb2.FieldType.FIELD_TYPE_DOUBLE_ARRAY
       if values.dtype == np.int32:
           return field_data_pb2.FieldType.FIELD_TYPE_INT_ARRAY
       if values.dtype == np.int64:
           return field_data_pb2.FieldType.FIELD_TYPE_LONG_ARRAY
       raise TypeError(f"Unsupported dtype: {values.dtype}")

   def build_set_stream(name, domain_id, zone_id_to_values, chunk_size=256 * 1024):
       yield svar_pb2.SetSolutionVariableDataRequest(
           header=svar_pb2.SolutionVariableHeader(name=name, domain_id=domain_id)
       )
       for zone_id, zone_values in zone_id_to_values.items():
           values = np.asarray(zone_values)
           max_per_chunk = max(1, chunk_size // values.dtype.itemsize)
           n_chunks = int(math.ceil(values.size / max_per_chunk))
           chunks = np.array_split(values, n_chunks) if values.size else []

           yield svar_pb2.SetSolutionVariableDataRequest(
               payload_info=svar_pb2.Info(
                   field_type=_field_type_for_array(values),
                   field_size=values.size,
                   zone=zone_id,
               )
           )
           for chunk in chunks:
               if chunk.size > 0:
                   yield svar_pb2.SetSolutionVariableDataRequest(
                       payload=_payload_for_array(chunk)
                   )

   zone_data = {
       12: np.full(1000, 500.0, dtype=np.float64),
       34: np.full(2000, 600.0, dtype=np.float64),
   }
   stub.SetSolutionVariableData(
       build_set_stream(name="SV_P", domain_id=1, zone_id_to_values=zone_data),
       metadata=metadata,
   )

See also
--------

- :doc:`field_data` — surface and mesh field streaming; defines the shared
  payload types (``DoublePayload``, ``FloatPayload``, etc.) and ``FieldType`` enum
- :doc:`reduction` — on-demand scalar reductions (area average, force, etc.)
  without streaming raw arrays
