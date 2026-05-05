Monitor
=======

The ``Monitor`` service provides RPCs to query monitor metadata and stream live monitor data during a Fluent simulation.

Overview
~~~~~~~~

.. include:: ../../shared_example_assumptions.rst

The ``Monitor`` service allows you to:

- Retrieve all monitor set definitions (names, labels, types, and units)
- Stream live x/y monitor data as the solver iterates
- Filter streams by x-axis type, monitor name, or sampling frequency
- Observe both residual and solution monitors

Monitors are grouped into *monitor sets*. A monitor set contains one or more named monitor signals
(e.g. ``residual-continuity``, ``mass-flow-outlet``) that share the same x-axis (iteration or time),
y-axis label, and unit information.

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.monitor``

**Main Classes:**

- ``MonitorStub``: Client stub for all monitor operations
- ``GetMonitorsRequest`` / ``GetMonitorsResponse``: Metadata query messages
- ``StreamingRequest`` / ``StreamingResponse``: Streaming messages
- ``MonitorSet``: Description of a monitor group
- ``MonitorFilter``: Optional filter applied to the data stream
- ``MonitorData``: Single y-axis sample (name + value)
- ``XAxisData``: Single x-axis sample (type + index)
- ``UnitData``: Unit conversion metadata attached to a monitor set

Key types
~~~~~~~~~

**MonitorType Enum**

.. list-table::
   :header-rows: 1

   * - Value
     - Name
     - Description
   * - 0
     - MONITOR_TYPE_UNSPECIFIED
     - Default; do not use
   * - 1
     - MONITOR_TYPE_RESIDUAL
     - Solver residual monitors
   * - 2
     - MONITOR_TYPE_SOLUTION
     - Solution / report monitors

**XAxisType Enum**

.. list-table::
   :header-rows: 1

   * - Value
     - Name
     - Description
   * - 0
     - XAXIS_TYPE_UNSPECIFIED
     - Default; do not use
   * - 1
     - XAXIS_TYPE_ITERATION
     - X axis represents solver iteration
   * - 2
     - XAXIS_TYPE_TIME
     - X axis represents physical time

**MonitorSet Fields**

.. list-table::
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - name
     - string
     - Unique identifier for the monitor set
   * - title
     - string
     - Human-readable title
   * - x_label
     - string
     - X-axis display label
   * - y_label
     - string
     - Y-axis display label
   * - frequency
     - sint64
     - Sampling frequency (every N iterations/time-steps)
   * - type
     - MonitorType
     - Residual or solution monitor
   * - unit_info
     - UnitData
     - Unit name, label, factor and offset
   * - axis
     - XAxisType
     - Iteration or time x-axis
   * - monitors
     - repeated string
     - Individual monitor signal names in this set

**MonitorFilter Fields**

.. list-table::
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - x_axis_type
     - XAxisType
     - Limit stream to iteration or time samples
   * - monitor_names
     - repeated string
     - Limit stream to specific monitor names
   * - frequency
     - sint32
     - Limit stream to a specific sampling frequency

RPC operations
~~~~~~~~~~~~~~

GetMonitors
-----------

Returns all monitor set definitions currently registered with the solver.
Call this before ``BeginStreaming`` to discover available monitor names and their metadata.

.. code-block:: python
   :caption: Python

   response = monitor_stub.GetMonitors(
       monitor_pb2.GetMonitorsRequest(),
       metadata=metadata,
   )

   for ms in response.monitor_sets:
       print(f"{ms.name}: {ms.title} (type={ms.type}, axis={ms.axis})")
       print(f"  Monitors: {ms.monitors}")

BeginStreaming
--------------

Opens a server-side streaming RPC that emits ``StreamingResponse`` messages as the solver
produces new monitor samples. Each response contains one ``XAxisData`` point and one or more
``MonitorData`` y-values.

``StreamingRequest`` has one optional field:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Field
     - Type
     - Description
   * - ``filters``
     - ``repeated MonitorFilter``
     - Zero or more filters. If empty, all monitor data is streamed. Each
       ``MonitorFilter`` can restrict by ``x_axis_type``, ``monitor_names``,
       or ``frequency``.

.. code-block:: python
   :caption: Python

   # Stream all monitors (no filter)
   request = monitor_pb2.StreamingRequest()

   for sample in monitor_stub.BeginStreaming(request, metadata=metadata):
       x = sample.x_axis_data
       for y in sample.y_axis_values:
           print(f"  iter={x.x_axis_index}  {y.name}={y.value:.6g}")

   # Stream only residual monitors on the iteration axis
   filtered_request = monitor_pb2.StreamingRequest(
       filters=[
           monitor_pb2.MonitorFilter(
               x_axis_type=monitor_pb2.XAXIS_TYPE_ITERATION,
           )
       ]
   )
   for sample in monitor_stub.BeginStreaming(filtered_request, metadata=metadata):
       x = sample.x_axis_data
       for y in sample.y_axis_values:
           print(f"  iter={x.x_axis_index}  {y.name}={y.value:.6g}")

Individual examples
~~~~~~~~~~~~~~~~~~~

List all monitor sets
---------------------

Discover every monitor set registered with the running solver:

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import monitor_pb2, monitor_pb2_grpc

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   channel = grpc.insecure_channel(f"{HOST}:{PORT}")
   metadata = [("password", PASSWORD)]
   stub = monitor_pb2_grpc.MonitorStub(channel)

   try:
       response = stub.GetMonitors(
           monitor_pb2.GetMonitorsRequest(),
           metadata=metadata,
       )

       type_names = {
           monitor_pb2.MONITOR_TYPE_RESIDUAL: "Residual",
           monitor_pb2.MONITOR_TYPE_SOLUTION: "Solution",
       }
       axis_names = {
           monitor_pb2.XAXIS_TYPE_ITERATION: "Iteration",
           monitor_pb2.XAXIS_TYPE_TIME: "Time",
       }

       for ms in response.monitor_sets:
           print(f"[{type_names.get(ms.type, '?')}] {ms.name} — {ms.title}")
           print(f"  x-axis: {axis_names.get(ms.axis, '?')}, frequency: {ms.frequency}")
           print(f"  y-label: {ms.y_label}")
           print(f"  monitors: {', '.join(ms.monitors)}")
           if ms.unit_info.unit:
               print(f"  unit: {ms.unit_info.unit} (factor={ms.unit_info.factor})")
   finally:
       channel.close()

Inspect unit information
------------------------

Read the unit conversion metadata attached to each monitor set:

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import monitor_pb2, monitor_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = monitor_pb2_grpc.MonitorStub(channel)

   try:
       response = stub.GetMonitors(
           monitor_pb2.GetMonitorsRequest(),
           metadata=metadata,
       )

       for ms in response.monitor_sets:
           u = ms.unit_info
           if u.name:
               print(f"{ms.name}: unit_name={u.name}, label={u.unit}, "
                     f"factor={u.factor}, offset={u.offset}")
   finally:
       channel.close()

Stream all monitor data
-----------------------

Receive every sample emitted by the solver until the stream ends:

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import monitor_pb2, monitor_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = monitor_pb2_grpc.MonitorStub(channel)

   try:
       for sample in stub.BeginStreaming(
           monitor_pb2.StreamingRequest(),
           metadata=metadata,
       ):
           x = sample.x_axis_data
           for y in sample.y_axis_values:
               print(f"iter={x.x_axis_index}  {y.name}={y.value:.6g}")
   except grpc.RpcError as err:
       print(f"Stream ended: {err.code()} - {err.details()}")
   finally:
       channel.close()

Stream only residuals (filtered)
--------------------------------

Use ``MonitorFilter`` to receive only iteration-based residual samples:

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import monitor_pb2, monitor_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = monitor_pb2_grpc.MonitorStub(channel)

   residual_filter = monitor_pb2.MonitorFilter(
       x_axis_type=monitor_pb2.XAXIS_TYPE_ITERATION
   )

   request = monitor_pb2.StreamingRequest(filters=[residual_filter])

   try:
       for sample in stub.BeginStreaming(
           request,
           metadata=metadata,
       ):
           x = sample.x_axis_data
           for y in sample.y_axis_values:
               print(f"iter={x.x_axis_index}  {y.name}={y.value:.6e}")
   except grpc.RpcError as err:
       print(f"Stream ended: {err.code()} - {err.details()}")
   finally:
       channel.close()

Stream specific monitors by name
--------------------------------

Filter the stream to a named subset of monitors:

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import monitor_pb2, monitor_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = monitor_pb2_grpc.MonitorStub(channel)

   name_filter = monitor_pb2.MonitorFilter(
       monitor_names=["continuity", "x-velocity", "energy"]
   )

   request = monitor_pb2.StreamingRequest(filters=[name_filter])

   try:
       for sample in stub.BeginStreaming(
           request,
           metadata=metadata,
       ):
           x = sample.x_axis_data
           for y in sample.y_axis_values:
               print(f"iter={x.x_axis_index}  {y.name}={y.value:.6e}")
   except grpc.RpcError as err:
       print(f"Stream ended: {err.code()} - {err.details()}")
   finally:
       channel.close()

Complete end-to-end example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A full workflow that connects to Fluent, discovers all monitors, then streams and summarises
convergence data until the solver finishes:

.. code-block:: python
   :caption: Python

   import grpc
   from collections import defaultdict
   from ansys.api.fluent.v1 import (
       health_pb2,
       health_pb2_grpc,
       monitor_pb2,
       monitor_pb2_grpc,
   )

   HOST = "127.0.0.1"
   PORT = 50051
   PASSWORD = "your-server-password"

   def run():
       channel = grpc.insecure_channel(f"{HOST}:{PORT}")
       metadata = [("password", PASSWORD)]

       try:
           # -- Step 1: health check ----------------------------------------
           health_stub = health_pb2_grpc.HealthStub(channel)
           health_resp = health_stub.Check(
               health_pb2.HealthCheckRequest(),
               metadata=metadata,
           )
           if health_resp.status != 1:  # 1 == SERVING
               raise RuntimeError("Server is not ready")
           print("? Server healthy")

           # -- Step 2: discover monitors -----------------------------------
           monitor_stub = monitor_pb2_grpc.MonitorStub(channel)
           monitors_resp = monitor_stub.GetMonitors(
               monitor_pb2.GetMonitorsRequest(),
               metadata=metadata,
           )

           type_label = {
               monitor_pb2.MONITOR_TYPE_RESIDUAL: "Residual",
               monitor_pb2.MONITOR_TYPE_SOLUTION: "Solution",
           }

           all_monitor_names = []
           print("\n-- Monitor sets ----------------------------------------------")
           for ms in monitors_resp.monitor_sets:
               kind = type_label.get(ms.type, "Unknown")
               print(f"  [{kind}] {ms.name}: {ms.monitors}")
               all_monitor_names.extend(ms.monitors)

           if not all_monitor_names:
               print("No monitors available - is a case loaded?")
               return

           # -- Step 3: stream and summarise --------------------------------
           print("\n-- Streaming monitor data (Ctrl-C to stop) ------------------")

           # Store the last value seen for each monitor name
           last_values: dict[str, float] = {}
           # Track min/max per monitor
           stats: dict[str, dict] = defaultdict(lambda: {"min": None, "max": None, "count": 0})

           request = monitor_pb2.StreamingRequest()

           try:
               for sample in monitor_stub.BeginStreaming(
                   request,
                   metadata=metadata,
               ):
                   x = sample.x_axis_data
                   axis_label = (
                       "iter" if x.x_axis_type == monitor_pb2.XAXIS_TYPE_ITERATION else "t"
                   )

                   for y in sample.y_axis_values:
                       last_values[y.name] = y.value
                       s = stats[y.name]
                       s["count"] += 1
                       s["min"] = y.value if s["min"] is None else min(s["min"], y.value)
                       s["max"] = y.value if s["max"] is None else max(s["max"], y.value)

                   # Print a one-line summary every sample
                   line_parts = [f"{axis_label}={x.x_axis_index}"]
                   for name, val in last_values.items():
                       line_parts.append(f"{name}={val:.4e}")
                   print("  " + "  ".join(line_parts))

           except grpc.RpcError as err:
               # OUT_OF_RANGE is the normal end-of-stream signal from Fluent
               if err.code() == grpc.StatusCode.OUT_OF_RANGE:
                   print("\n? Solver finished - stream closed normally")
               else:
                   print(f"\n? Stream error: {err.code()} - {err.details()}")
                   raise

           # -- Step 4: print summary ----------------------------------------
           print("\n-- Convergence summary ---------------------------------------")
           for name, s in stats.items():
               print(
                   f"  {name:40s}  samples={s['count']:4d}"
                   f"  min={s['min']:.4e}  max={s['max']:.4e}"
               )

       except grpc.RpcError as err:
           print(f"RPC error: {err.code()} - {err.details()}")
           raise
       finally:
           channel.close()

   if __name__ == "__main__":
       run()

Best practices
~~~~~~~~~~~~~~

1. **Call GetMonitors before BeginStreaming** — use the returned monitor names to build
   targeted ``MonitorFilter`` objects rather than receiving every signal.

2. **Handle** ``OUT_OF_RANGE`` **gracefully** — Fluent signals end-of-stream with this
   gRPC status code; treat it as a normal exit, not an error.

3. **Distinguish residual from solution monitors** — residuals typically decrease monotonically
   and are useful for convergence checks; solution monitors track physical quantities.

4. **Apply filters for large cases** — streaming all monitors in a case with many solution
   monitors can produce high message rates; filter by name or frequency to reduce load.

5. **Close the channel in a** ``finally`` **block** — always release gRPC resources even
   when the stream is interrupted.

See also
--------

- :doc:`../../getting_started/gettingstarted` — basic client setup
- :doc:`events` — structured solver lifecycle events (iteration signals, pause callbacks)
- :doc:`reduction` — on-demand scalar reductions over surfaces and zones

.. ----------------------------------------------------------------------------
.. The block below is generated by docs/_ext/proto_docgen.py from the matching
.. .proto file in ansys/api/fluent/v1. Edit the proto comments to update it.
.. ----------------------------------------------------------------------------
