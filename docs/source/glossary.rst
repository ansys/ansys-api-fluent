Glossary
========

.. glossary::

    Channel
        A gRPC connection to a server. Created with ``grpc.insecure_channel()`` or ``grpc.secure_channel()``.

    Metadata
        Additional information sent with gRPC requests, typically including authentication credentials like passwords.

    Stub
        A client object that provides methods to call remote procedures. Created from a service definition.

    RPC
        Remote Procedure Call - a method on a service that can be called over gRPC.

    Service
        A collection of related RPC operations, defined in a .proto file.

    Message
        A data structure defined in a .proto file. Request and response messages are used with RPCs.

    Stream
        A sequence of messages returned by an RPC. Server streams return multiple responses over time.

    Payload
        The actual data content in a response, often numeric field values in FieldData responses.

    Surface
        A geometric surface in the mesh (e.g., wall, inlet, outlet) where field data can be requested.

    Field Data
        Simulation results (temperature, pressure, velocity) associated with mesh elements or nodes.

    Node Values
        Field data stored at mesh vertices/nodes.

    Element Values
        Field data stored at cell centers (averaged to cell centers).

    gRPC
        A modern RPC framework using Protocol Buffers for serialization and HTTP/2 for transport.

    Protocol Buffers
        A language-neutral, platform-neutral method of serializing structured data.

    Package
        A namespace for message and service definitions, used to organize proto definitions.

    DataModel
        Fluent's API for accessing and modifying configuration and state.

    TUI
        Text User Interface - the command-line interface for Fluent.
