Events
======

The Events service provides server-streamed notifications for solver lifecycle,
file I/O, progress, and data-model activity.

Overview
~~~~~~~~

.. include:: ../shared_example_assumptions.rst

The ``Events`` service allows you to:

- Start a persistent event stream from Fluent
- Receive typed event payloads using a ``oneof`` union
- Track solver progress (iterations, timesteps, completion percent)
- Observe case/data read operations and initialization lifecycle
- React to pause/resume, auto-pause, and command completion signals
- Monitor data-model and report/plot changes

Service definition
~~~~~~~~~~~~~~~~~~

**Package:** ``ansys.api.fluent.v1.events``

**Main Classes:**

- ``EventsStub``: Client stub for event operations
- ``BeginStreamingRequest``: Request message to start the stream
- ``BeginStreamingResponse``: Streamed response carrying one event in ``oneof as``

Core RPC operations
~~~~~~~~~~~~~~~~~~~

BeginStreaming (server stream)
------------------------------

Starts the event stream and yields a sequence of
``BeginStreamingResponse`` messages.

.. code-block:: python

    stream = events_stub.BeginStreaming(
          events_pb2.BeginStreamingRequest(),
          metadata=metadata,
    )

    for response in stream:
          event_type = response.WhichOneof("as")
          print(f"Received event: {event_type}")

Working with ``oneof`` events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each streamed ``BeginStreamingResponse`` has exactly one populated event in the
``as`` union. Use ``WhichOneof('as')`` to identify which event is present, then
access the matching field.

.. code-block:: python

    response = next(stream)
    event_type = response.WhichOneof("as")

    if event_type == "iteration_started_event":
          print(response.iteration_started_event.index)
    elif event_type == "progress_event":
          print(response.progress_event.percent_complete)
    elif event_type == "error_event":
          print(response.error_event.message)

Event types in ``BeginStreamingResponse``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Event union fields
    :header-rows: 1
    :widths: 32 28 40

    * - Field in ``oneof as``
       - Payload message
       - Typical meaning
    * - ``pre_read_case_event``
       - ``PreReadCaseEvent``
       - Case file read is about to start
    * - ``case_read_event``
       - ``CaseReadEvent``
       - Case file read completed
    * - ``pre_initialize_event``
       - ``PreInitializeEvent``
       - Initialization is about to begin
    * - ``initialized_event``
       - ``InitializedEvent``
       - Initialization completed
    * - ``pre_read_data_event``
       - ``PreReadDataEvent``
       - Data file read is about to start
    * - ``data_read_event``
       - ``DataReadEvent``
       - Data file read completed
    * - ``iteration_started_event``
       - ``IterationStartedEvent``
       - Iteration start, includes ``index``
    * - ``iteration_ended_event``
       - ``IterationEndedEvent``
       - Iteration end, includes ``index``
    * - ``timestep_started_event``
       - ``TimestepStartedEvent``
       - Time step start, includes ``index`` and ``size``
    * - ``timestep_ended_event``
       - ``TimestepEndedEvent``
       - Time step end, includes ``index`` and ``size``
    * - ``calculations_started_event``
       - ``CalculationsStartedEvent``
       - Solver calculations started
    * - ``calculations_ended_event``
       - ``CalculationsEndedEvent``
       - Solver calculations ended
    * - ``report_definition_changed_event``
       - ``ReportDefinitionChangedEvent``
       - A report definition changed
    * - ``plot_set_changed_event``
       - ``PlotSetChangedEvent``
       - A plot set changed
    * - ``residual_plot_changed_event``
       - ``ResidualPlotChangedEvent``
       - Residual plot settings changed
    * - ``clear_settings_done_event``
       - ``ClearSettingsDoneEvent``
       - Clear-settings operation completed
    * - ``auto_pause_event``
       - ``AutoPauseEvent``
       - Auto-pause reached a trigger condition
    * - ``calculations_paused_event``
       - ``CalculationsPausedEvent``
       - Calculations paused
    * - ``calculations_resumed_event``
       - ``CalculationsResumedEvent``
       - Calculations resumed
    * - ``progress_event``
       - ``ProgressEvent``
       - Percent complete and progress message
    * - ``error_event``
       - ``ErrorEvent``
       - Fatal error details
    * - ``command_completed_event``
       - ``CommandCompletedEvent``
       - Command finished
    * - ``data_model_changed_event``
       - ``DataModelChangedEvent``
       - One or more data-model paths changed
    * - ``solver_time_estimate_event``
       - ``SolverTimeEstimateEvent``
       - Estimated remaining time

Complete example
~~~~~~~~~~~~~~~~

An end-to-end event listener that streams events, decodes event types,
prints key payload fields, and handles stream failures.

.. code-block:: python

    import grpc
    from ansys.api.fluent.v1 import events_pb2, events_pb2_grpc

    HOST = "127.0.0.1"
    PORT = 50051
    PASSWORD = "your-server-password"

    def format_event(response):
          event_type = response.WhichOneof("as")

          if event_type == "iteration_started_event":
                ev = response.iteration_started_event
                return f"iteration_started index={ev.index}"
          if event_type == "iteration_ended_event":
                ev = response.iteration_ended_event
                return f"iteration_ended index={ev.index}"
          if event_type == "timestep_started_event":
                ev = response.timestep_started_event
                return f"timestep_started index={ev.index} size={ev.size}"
          if event_type == "timestep_ended_event":
                ev = response.timestep_ended_event
                return f"timestep_ended index={ev.index} size={ev.size}"
          if event_type == "progress_event":
                ev = response.progress_event
                return f"progress {ev.percent_complete}%: {ev.message}"
          if event_type == "solver_time_estimate_event":
                ev = response.solver_time_estimate_event
                return (
                      "solver_time_estimate "
                      f"{ev.hours:.0f}h {ev.minutes:.0f}m {ev.seconds:.1f}s"
                )
          if event_type == "error_event":
                ev = response.error_event
                return f"error code={ev.error_code}: {ev.message}"
          if event_type == "pre_read_case_event":
                ev = response.pre_read_case_event
                return f"pre_read_case path={ev.case_file_path}"
          if event_type == "case_read_event":
                ev = response.case_read_event
                return f"case_read path={ev.case_file_path}"
          if event_type == "pre_read_data_event":
                ev = response.pre_read_data_event
                return f"pre_read_data path={ev.data_file_path}"
          if event_type == "data_read_event":
                ev = response.data_read_event
                return f"data_read path={ev.data_file_path}"
          if event_type == "data_model_changed_event":
                ev = response.data_model_changed_event
                return f"data_model_changed paths={list(ev.paths)}"

          # Zero-payload event notifications
          return event_type or "unknown_event"


    def stream_events(max_events=200):
          channel = grpc.insecure_channel(f"{HOST}:{PORT}")
          metadata = [("password", PASSWORD)]
          stub = events_pb2_grpc.EventsStub(channel)

          try:
                stream = stub.BeginStreaming(
                      events_pb2.BeginStreamingRequest(),
                      metadata=metadata,
                )

                print("Listening for Fluent events...")
                for i, response in enumerate(stream, start=1):
                      print(f"[{i}] {format_event(response)}")

                      # Stop after N events for demo purposes.
                      if i >= max_events:
                            break

          except grpc.RpcError as err:
                print(f"Event stream error: {err.code()} - {err.details()}")
                raise
          finally:
                channel.close()


    if __name__ == "__main__":
          stream_events(max_events=200)

Best practices
~~~~~~~~~~~~~~

1. **Dispatch via ``WhichOneof``** - Always detect the active ``oneof`` field before reading payload data.
2. **Handle ``RpcError`` robustly** - Network interruptions and server restarts can terminate streams.
3. **Design for reconnect** - Production listeners should reconnect with backoff after failures.
4. **Keep handlers lightweight** - Avoid expensive work in the stream loop; offload to worker queues when needed.
5. **Treat ``error_event`` specially** - Log and surface fatal errors immediately.
6. **Limit demo streams** - In examples/tests, stop after N events to avoid endless runs.
7. **Ignore ``client_execute_event`` in end-user clients** - This event is reserved for internal workflows and is not part of the public end-user event contract.

See also
~~~~~~~~

- :doc:`../gettingstarted` - Basic client setup
- :doc:`field_data` - Field data retrieval service
- :doc:`health` - Health service for connectivity checks
