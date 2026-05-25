Solver output streams — events, monitors, and transcript
=========================================================

Python client examples for the ``Transcript``, ``Events``, and ``Monitor``
gRPC services.

See :doc:`../../api/services/transcript`, :doc:`../../api/services/events`,
and :doc:`../../api/services/monitor`
for these services' complete reference material.

.. include:: ../../shared_example_assumptions.rst

.. code-block:: python
   :caption: Python

   import grpc
   from ansys.api.fluent.v1 import (
       events_pb2, events_pb2_grpc,
       monitor_pb2, monitor_pb2_grpc,
       transcript_pb2, transcript_pb2_grpc,
   )

   channel = grpc.insecure_channel("127.0.0.1:50051")
   metadata = [("password", "your-server-password")]

   transcript_stub = transcript_pb2_grpc.TranscriptStub(channel)
   events_stub = events_pb2_grpc.EventsStub(channel)
   monitor_stub = monitor_pb2_grpc.MonitorStub(channel)

Opening a transcript stream
-----------------------------

``Transcript.BeginStreaming`` opens a server-streaming call; each response
carries one line (or chunk) of Fluent console output in ``resp.transcript``.

.. code-block:: python
   :caption: Python

   stream = transcript_stub.BeginStreaming(
       transcript_pb2.TranscriptRequest(),
       metadata=metadata,
   )
   print(stream is not None)  # -> True
   stream.cancel()

Opening two independent transcript streams
-------------------------------------------

Multiple simultaneous ``BeginStreaming`` calls return independent stream
objects and can be cancelled separately.

.. code-block:: python
   :caption: Python

   stream1 = transcript_stub.BeginStreaming(
       transcript_pb2.TranscriptRequest(), metadata=metadata
   )
   stream2 = transcript_stub.BeginStreaming(
       transcript_pb2.TranscriptRequest(), metadata=metadata
   )
   print(stream1 is not stream2)  # -> True
   stream1.cancel()
   stream2.cancel()

Cancelling a transcript stream
--------------------------------

Cancelling a stream and then iterating it raises ``grpc.StatusCode.CANCELLED``
or ``StopIteration`` — both are normal.

.. code-block:: python
   :caption: Python

   stream = transcript_stub.BeginStreaming(
       transcript_pb2.TranscriptRequest(),
       metadata=metadata,
   )
   stream.cancel()

   try:
       next(iter(stream))
   except grpc.RpcError as e:
       print(e.code() == grpc.StatusCode.CANCELLED)  # -> True
   except StopIteration:
       pass  # also acceptable

Opening an event stream
------------------------

``Events.BeginStreaming`` opens a server-streaming call; each response carries
exactly one event in its ``oneof as`` union.

.. code-block:: python
   :caption: Python

   stream = events_stub.BeginStreaming(
       events_pb2.BeginStreamingRequest(),
       metadata=metadata,
   )
   print(stream is not None)  # -> True
   stream.cancel()

Decoding event types
---------------------

Call ``WhichOneof("as")`` on each response to identify the event and then
access its payload fields.

.. code-block:: python
   :caption: Python

   valid_event_fields = {
       "pre_read_case_event", "case_read_event",
       "pre_initialize_event", "initialized_event",
       "pre_read_data_event", "data_read_event",
       "iteration_started_event", "iteration_ended_event",
       "timestep_started_event", "timestep_ended_event",
       "calculations_started_event", "calculations_ended_event",
       "report_definition_changed_event", "plot_set_changed_event",
       "residual_plot_changed_event", "clear_settings_done_event",
       "auto_pause_event", "calculations_paused_event",
       "calculations_resumed_event", "progress_event",
       "error_event", "command_completed_event",
       "data_model_changed_event", "solver_time_estimate_event",
       "client_execute_event",
   }

   stream = events_stub.BeginStreaming(
       events_pb2.BeginStreamingRequest(),
       metadata=metadata,
   )
   for event_response in stream:
       kind = event_response.WhichOneof("as")
       if kind is not None:
           print(kind in valid_event_fields)  # -> True
       if kind == "iteration_ended_event":
           print(event_response.iteration_ended_event.index)    # -> 1
       elif kind == "progress_event":
           progress_event_data = event_response.progress_event
           print(progress_event_data.percent_complete, progress_event_data.message)     # -> 12.5  'Solving...'
       elif kind == "solver_time_estimate_event":
           time_estimate_event = event_response.solver_time_estimate_event
           print(time_estimate_event.hours, time_estimate_event.minutes, time_estimate_event.seconds)   # -> 0  2  34.5
       elif kind == "error_event":
           print(event_response.error_event.message)            # -> 'Diverged'
       break
   stream.cancel()

Registering a pause trigger
-----------------------------

``PauseSolveFor`` registers a pause that fires after each iteration or time
step; it returns a unique ``registration_id``.

.. code-block:: python
   :caption: Python

   pause_registration = events_stub.PauseSolveFor(
       events_pb2.PauseSolveForRequest(
           solution_event=events_pb2.SOLUTION_EVENT_ITERATION
       ),
       metadata=metadata,
   )
   print(isinstance(pause_registration.registration_id, int))  # -> True
   print(pause_registration.registration_id > 0)               # -> True

   # Register a second trigger — IDs must be distinct.
   second_pause_registration = events_stub.PauseSolveFor(
       events_pb2.PauseSolveForRequest(
           solution_event=events_pb2.SOLUTION_EVENT_ITERATION
       ),
       metadata=metadata,
   )
   print(pause_registration.registration_id != second_pause_registration.registration_id)  # -> True

Registering a time-step pause trigger
---------------------------------------

``SOLUTION_EVENT_TIME_STEP`` fires at the end of each time step in a
transient simulation.

.. code-block:: python
   :caption: Python

   timestep_pause_registration = events_stub.PauseSolveFor(
       events_pb2.PauseSolveForRequest(
           solution_event=events_pb2.SOLUTION_EVENT_TIME_STEP
       ),
       metadata=metadata,
   )
   print(timestep_pause_registration.registration_id > 0)  # -> True

Cancelling a pause registration
---------------------------------

``CancelPauseSolve`` removes a previously registered pause trigger.

.. code-block:: python
   :caption: Python

   cancel_response = events_stub.CancelPauseSolve(
       events_pb2.CancelPauseSolveRequest(
           registration_id=pause_registration.registration_id
       ),
       metadata=metadata,
   )
   print(cancel_response is not None)  # -> True

   # Clean up the other registrations.
   events_stub.CancelPauseSolve(
       events_pb2.CancelPauseSolveRequest(registration_id=second_pause_registration.registration_id),
       metadata=metadata,
   )
   events_stub.CancelPauseSolve(
       events_pb2.CancelPauseSolveRequest(registration_id=timestep_pause_registration.registration_id),
       metadata=metadata,
   )

Resuming the solver
--------------------

``ResumeSolve`` unpauses a session that was suspended by a ``PauseSolveFor``
registration; passing an unknown ID is accepted without raising an error.

.. code-block:: python
   :caption: Python

   events_stub.ResumeSolve(
       events_pb2.ResumeSolveRequest(registration_id=999999999),
       metadata=metadata,
   )

Discovering monitor sets
-------------------------

``GetMonitors`` enumerates every monitor set registered with the solver,
including its name, type, x-axis type, update frequency, and unit metadata.

.. code-block:: python
   :caption: Python

   monitors_response = monitor_stub.GetMonitors(
       monitor_pb2.GetMonitorsRequest(),
       metadata=metadata,
   )
   for ms in monitors_response.monitor_sets:
       print(ms.name)       # -> 'residuals'
       print(ms.monitors)   # -> ['continuity', 'x-velocity', 'energy']
       print(ms.frequency)  # -> 1
       print(ms.type in {
           monitor_pb2.MONITOR_TYPE_RESIDUAL,
           monitor_pb2.MONITOR_TYPE_SOLUTION,
           monitor_pb2.MONITOR_TYPE_UNSPECIFIED,
       })                   # -> True
       print(ms.axis in {
           monitor_pb2.XAXIS_TYPE_ITERATION,
           monitor_pb2.XAXIS_TYPE_TIME,
           monitor_pb2.XAXIS_TYPE_UNSPECIFIED,
       })                   # -> True

Validating monitor set metadata
---------------------------------

Every monitor set must have a non-empty name, at least one monitor entry,
and a non-negative frequency; ``unit_info.factor`` is non-negative when set.

.. code-block:: python
   :caption: Python

   # Two consecutive calls must return identical monitor set names.
   first_monitors_response = monitor_stub.GetMonitors(
       monitor_pb2.GetMonitorsRequest(), metadata=metadata
   )
   second_monitors_response = monitor_stub.GetMonitors(
       monitor_pb2.GetMonitorsRequest(), metadata=metadata
   )
   names1 = sorted(ms.name for ms in first_monitors_response.monitor_sets)
   names2 = sorted(ms.name for ms in second_monitors_response.monitor_sets)
   print(names1 == names2)  # -> True

   for ms in first_monitors_response.monitor_sets:
       print(len(ms.name) > 0)         # -> True
       print(len(ms.monitors) > 0)     # -> True
       print(ms.frequency >= 0)        # -> True
       if ms.unit_info.unit:
           print(ms.unit_info.factor >= 0)  # -> True

Opening a monitor stream
-------------------------

``Monitor.BeginStreaming`` streams live y-axis samples; each response contains
an ``XAxisData`` point and one or more ``MonitorData`` entries.

.. code-block:: python
   :caption: Python

   stream = monitor_stub.BeginStreaming(
       monitor_pb2.StreamingRequest(),
       metadata=metadata,
   )
   print(stream is not None)  # -> True
   stream.cancel()

Reading monitor samples
------------------------

Each ``StreamingResponse`` exposes ``x_axis_data`` (index and type) and
``y_axis_values`` (name + float value per monitored quantity).

.. code-block:: python
   :caption: Python

   stream = monitor_stub.BeginStreaming(
       monitor_pb2.StreamingRequest(),
       metadata=metadata,
   )
   sample = next(iter(stream))
   stream.cancel()

   print(hasattr(sample, "x_axis_data"))                 # -> True
   print(sample.x_axis_data.x_axis_type in {
       monitor_pb2.XAXIS_TYPE_ITERATION,
       monitor_pb2.XAXIS_TYPE_TIME,
       monitor_pb2.XAXIS_TYPE_UNSPECIFIED,
   })                                                     # -> True
   for y in sample.y_axis_values:
       print(len(y.name) > 0)                            # -> True
       print(isinstance(y.value, float))                 # -> True
       print(f"{y.name} = {y.value:.4e}")
   # -> continuity = 9.8765e-03
   # -> x-velocity = 4.3210e-04
   # -> energy     = 1.2345e-06

Filtering the monitor stream
------------------------------

Pass a ``MonitorFilter`` with ``x_axis_type`` to receive only iteration- or
time-based samples.

.. code-block:: python
   :caption: Python

   stream = monitor_stub.BeginStreaming(
       monitor_pb2.StreamingRequest(
           filters=[
               monitor_pb2.MonitorFilter(
                   x_axis_type=monitor_pb2.XAXIS_TYPE_ITERATION
               )
           ]
       ),
       metadata=metadata,
   )
   print(stream is not None)  # -> True
   stream.cancel()

Cancelling a monitor stream
-----------------------------

Cancelling a monitor stream and then iterating it raises
``grpc.StatusCode.CANCELLED`` or ``StopIteration`` — both are normal.

.. code-block:: python
   :caption: Python

   stream = monitor_stub.BeginStreaming(
       monitor_pb2.StreamingRequest(),
       metadata=metadata,
   )
   stream.cancel()

   try:
       next(iter(stream))
   except grpc.RpcError as e:
       print(e.code() == grpc.StatusCode.CANCELLED)  # -> True
   except StopIteration:
       pass  # also acceptable

See :doc:`../../api/services/transcript`, :doc:`../../api/services/events`,
and :doc:`../../api/services/monitor` for the complete reference material.
