Solver output streams — events, monitors, and transcript
=========================================================

Three services push live data from Fluent to your client over gRPC server-side
streams. Use them together to observe a running simulation without polling:

- **Transcript** — raw console output, line by line.
- **Events** — typed notifications for solver lifecycle milestones (iterations,
  time steps, convergence, pause/resume, data-model changes, and more).
- **Monitor** — per-iteration or per-time-step y-axis samples for every
  residual and solution monitor registered with the solver.

For the full message and field reference see :doc:`../../api/services/transcript`,
:doc:`../../api/services/events`, and :doc:`../../api/services/monitor`.

.. include:: ../../shared_example_assumptions.rst

Transcript
----------

``Transcript.BeginStreaming`` opens a persistent stream that yields one
``TranscriptResponse`` per line (or chunk) of Fluent console output.
Run it in a daemon thread so your main logic is not blocked.

.. code-block:: python
   :caption: Python

   import threading
   import grpc
   from ansys.api.fluent.v1 import transcript_pb2, transcript_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = transcript_pb2_grpc.TranscriptStub(channel)

   stop = threading.Event()

   def _read_transcript():
       stream = stub.BeginStreaming(
           transcript_pb2.TranscriptRequest(), metadata=metadata
       )
       for resp in stream:
           if stop.is_set():
               break
           print(resp.transcript, end="", flush=True)

   t = threading.Thread(target=_read_transcript, daemon=True)
   t.start()

   # ... do other work, then signal the thread when done ...
   stop.set()

Events
------

``Events.BeginStreaming`` yields ``BeginStreamingResponse`` messages. Each
response carries exactly one event in its ``oneof as`` union. Call
``WhichOneof("as")`` to identify the active field, then read its payload.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import events_pb2, events_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = events_pb2_grpc.EventsStub(channel)

   stream = stub.BeginStreaming(
       events_pb2.BeginStreamingRequest(), metadata=metadata
   )

   for resp in stream:
       kind = resp.WhichOneof("as")

       if kind == "iteration_ended_event":
           print(f"iteration {resp.iteration_ended_event.index} complete")
       elif kind == "progress_event":
           ev = resp.progress_event
           print(f"  {ev.percent_complete:.1f}%  {ev.message}")
       elif kind == "calculations_ended_event":
           print("Solver finished")
           break
       elif kind == "error_event":
           raise RuntimeError(resp.error_event.message)

Pausing the solver at each iteration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``PauseSolveFor`` to register a pause trigger, perform work while the
solver is paused, then call ``ResumeSolve`` to continue. Cancel the
registration with ``CancelPauseSolve`` when you no longer need it.

.. code-block:: python
   :caption: Python

   # Register a pause after every iteration.
   reg = stub.PauseSolveFor(
       events_pb2.PauseSolveForRequest(
           solution_event=events_pb2.SOLUTION_EVENT_ITERATION
       ),
       metadata=metadata,
   )
   registration_id = reg.registration_id

   # The solver will pause after each iteration; resume it from the event stream.
   for resp in stream:
       if resp.WhichOneof("as") == "calculations_paused_event":
           print("Paused — doing per-iteration work...")
           # ... inspect solution, write checkpoint, etc. ...
           stub.ResumeSolve(
               events_pb2.ResumeSolveRequest(registration_id=registration_id),
               metadata=metadata,
           )

   # Remove the pause registration when done.
   stub.CancelPauseSolve(
       events_pb2.CancelPauseSolveRequest(registration_id=registration_id),
       metadata=metadata,
   )

Monitors
--------

Call ``Monitor.GetMonitors`` first to discover what monitor sets are
registered, then open a ``BeginStreaming`` call to receive live samples.
Each ``StreamingResponse`` contains one ``XAxisData`` point (iteration or
time index) and one or more ``MonitorData`` y-values.

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import monitor_pb2, monitor_pb2_grpc

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]
   stub = monitor_pb2_grpc.MonitorStub(channel)

   # Discover available monitor sets.
   monitors_resp = stub.GetMonitors(
       monitor_pb2.GetMonitorsRequest(), metadata=metadata
   )
   for ms in monitors_resp.monitor_sets:
       print(f"{ms.name}: {ms.monitors}")

   # Stream all monitor data until the solver finishes.
   try:
       for sample in stub.BeginStreaming(
           monitor_pb2.StreamingRequest(), metadata=metadata
       ):
           x = sample.x_axis_data
           for y in sample.y_axis_values:
               print(f"iter={x.x_axis_index}  {y.name}={y.value:.4e}")
   except grpc.RpcError as err:
       if err.code() == grpc.StatusCode.OUT_OF_RANGE:
           print("Solver finished — stream closed normally")
       else:
           raise

To receive only a named subset of monitors, pass a ``MonitorFilter``:

.. code-block:: python
   :caption: Python

   filt = monitor_pb2.MonitorFilter(
       monitor_names=["continuity", "x-velocity", "energy"]
   )
   for sample in stub.BeginStreaming(
       monitor_pb2.StreamingRequest(filters=[filt]), metadata=metadata
   ):
       x = sample.x_axis_data
       for y in sample.y_axis_values:
           print(f"iter={x.x_axis_index}  {y.name}={y.value:.4e}")

End-to-end example
------------------

The example below runs all three streams concurrently: transcript in a
background thread, events decoded in a second thread, and monitor data
read on the main thread until the solver exits.

.. code-block:: python
   :caption: Python

   import threading
   import grpc
   from ansys.api.fluent.v1 import (
       events_pb2, events_pb2_grpc,
       monitor_pb2, monitor_pb2_grpc,
       transcript_pb2, transcript_pb2_grpc,
   )

   HOST, PORT, PASSWORD = "127.0.0.1", 50051, "your-server-password"

   channel = grpc.insecure_channel(f"{HOST}:{PORT}")
   metadata = [("password", PASSWORD)]
   stop = threading.Event()

   # --- Transcript thread ---------------------------------------------------
   def _transcript():
       stub = transcript_pb2_grpc.TranscriptStub(channel)
       for resp in stub.BeginStreaming(
           transcript_pb2.TranscriptRequest(), metadata=metadata
       ):
           if stop.is_set():
               break
           print("[console]", resp.transcript, end="", flush=True)

   # --- Events thread -------------------------------------------------------
   def _events():
       stub = events_pb2_grpc.EventsStub(channel)
       for resp in stub.BeginStreaming(
           events_pb2.BeginStreamingRequest(), metadata=metadata
       ):
           if stop.is_set():
               break
           kind = resp.WhichOneof("as")
           if kind == "iteration_ended_event":
               print(f"[event] iteration {resp.iteration_ended_event.index} done")
           elif kind == "error_event":
               print(f"[event] ERROR: {resp.error_event.message}")
           elif kind == "calculations_ended_event":
               print("[event] calculations ended")
               stop.set()

   threading.Thread(target=_transcript, daemon=True).start()
   threading.Thread(target=_events, daemon=True).start()

   # --- Monitor data on main thread -----------------------------------------
   monitor_stub = monitor_pb2_grpc.MonitorStub(channel)
   try:
       for sample in monitor_stub.BeginStreaming(
           monitor_pb2.StreamingRequest(), metadata=metadata
       ):
           x = sample.x_axis_data
           for y in sample.y_axis_values:
               print(f"[monitor] iter={x.x_axis_index}  {y.name}={y.value:.4e}")
   except grpc.RpcError as err:
       if err.code() != grpc.StatusCode.OUT_OF_RANGE:
           raise
   finally:
       stop.set()
       channel.close()
