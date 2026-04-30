Glossary
========

.. glossary::

    API schema
        The complete description of available paths, parameter types, commands,
        queries, and help text returned by the ``GetSchema`` RPC. Both the
        DataModel service and the Settings service expose ``GetSchema``. Use the
        API schema to discover what is available before writing ``GetState`` or
        ``GetVar`` calls.

    Channel
        A gRPC connection to a Fluent server. Created with
        ``grpc.insecure_channel()`` or ``grpc.secure_channel()``.

    DataModel service
        The ``DataModel`` gRPC service (package ``ansys.api.fluent.v1.datamodel_se``).
        It exposes the Fluent object model as a tree of singletons, named objects,
        parameters, commands, and queries. Access it through the DataModel API.

    DataModel API
        The interface exposed by the DataModel service. A tree of named objects,
        singletons, parameters, commands, and queries that covers the meshing and
        solver object model. Addressed by ``rules`` context and slash-separated
        ``path`` strings.

    Element values
        Field data stored at cell centers (averaged to cell centers).

    Field data
        Simulation results (temperature, pressure, velocity) associated with mesh
        elements or nodes.

    gRPC
        A modern RPC framework using Protocol Buffers for serialization and
        HTTP/2 for transport.

    Message
        A data structure defined in a ``.proto`` file. Request and response
        messages are used with RPCs.

    Metadata
        Additional key-value pairs sent with every gRPC request, typically
        including the server password as ``[("password", PASSWORD)]``.

    Node values
        Field data stored at mesh vertices/nodes.

    Package
        A namespace for message and service definitions, used to organise proto
        definitions.

    Protocol Buffers
        A language-neutral, platform-neutral method of serializing structured data.
        Used by all Fluent v1 services.

    RPC
        Remote Procedure Call — a method on a service that can be called over gRPC.

    Service
        A collection of related RPC operations defined in a ``.proto`` file.

    Settings API
        The interface exposed by the Settings service. A flat, slash-separated
        path hierarchy (for example,
        ``setup/boundary-conditions/wall/wall-1/thermal``) that maps directly
        to Fluent solver configuration.

    Settings service
        The ``Settings`` gRPC service (package ``ansys.api.fluent.v1.settings``).
        It exposes Fluent simulation configuration as a hierarchical path tree.
        Access it through the Settings API.

    Stream
        A sequence of messages returned by a single RPC. Server-streaming RPCs
        return multiple responses over time (for example, event notifications or
        field data chunks).

    Stub
        A client object that provides methods to call remote procedures. Each
        service has a corresponding ``*Stub`` class generated from the proto
        definition.

    Surface
        A geometric surface in the mesh (for example, wall, inlet, outlet) where
        field data can be requested.

    ``Variant``
        The polymorphic value container used by the DataModel service. Supports
        ``bool_state``, ``int64_state``, ``double_state``, ``string_state``,
        ``variant_vector_state``, and ``variant_map_state``. Use
        ``WhichOneof("as")`` to determine which field is populated in a response.

    ``Value``
        The polymorphic value container used by the Settings service. Supports
        ``boolean``, ``integer``, ``real``, ``string``, ``value_list``, and
        ``value_map``. Use ``WhichOneof("value")`` to determine which field is
        populated in a response.

    Monitor service
        The ``Monitor`` gRPC service (package ``ansys.api.fluent.v1.monitor``).
        Provides ``GetMonitors`` to enumerate monitor set metadata and
        ``BeginStreaming`` to stream live residual and solution monitor values
        as the solver iterates.

    Monitor set
        A named group of one or more monitor signals that share the same x-axis
        (iteration or time), y-axis label, and unit information. Returned by
        ``GetMonitors``.

    Reduction service
        The ``Reduction`` gRPC service (package ``ansys.api.fluent.v1.reduction``).
        Computes scalar and vector reductions — area averages, volume integrals,
        forces, moments, extrema — over selected surfaces and cell zones without
        streaming raw field data.

    Solution Variables service
        The ``SolutionVariable`` gRPC service (package
        ``ansys.api.fluent.v1.solution_variable``).
        Provides metadata discovery (``GetZonesInfo``,
        ``GetSolutionVariableInfo``) and bidirectional streaming access
        (``GetSolutionVariableData``, ``SetSolutionVariableData``) to per-zone
        solution variable arrays.

    Transcript service
        The ``Transcript`` gRPC service (package ``ansys.api.fluent.v1.transcript``).
        Streams Fluent console output as a continuous server-side stream via
        ``BeginStreaming``.

    Connection service
        The ``Connection`` gRPC service (package ``ansys.api.fluent.v1.connection``).
        Manages the client session via a bidirectional ``Connect`` stream that
        handles authentication, version negotiation, and connection lifecycle.

    Chunk
        A single message within a server-streaming response that carries a
        portion of a larger dataset — for example, a ``DoublePayload`` message
        inside a ``GetFieldsResponse`` stream.

    Payload
        The numeric data content of a streaming chunk. Field Data and Solution
        Variables responses use ``DoublePayload``, ``FloatPayload``,
        ``IntPayload``, and ``LongPayload`` messages to carry typed arrays.

    Rules context
        A string (for example, ``"meshing"`` or ``"flserver"``) that identifies
        which DataModel API family to address. Passed as the ``rules`` field in
        every DataModel service request.

    PathInfo
        A message used by the Settings service to specify a settings node.
        Contains two fields: ``root`` (which Settings API family, typically
        ``"fluent"``) and ``path`` (slash-separated location within that root,
        for example ``setup/boundary-conditions/wall``).

    TUI
        Text User Interface — the legacy command-line interface for Fluent,
        accessible through the ``TextInterface`` service.
