# Fluent v1 gRPC Client User Guide

This guide shows how to use the packaged Python gRPC interface in
`ansys-api-fluent` to connect to a Fluent v1 gRPC server and call services
directly.

It is written as a self-contained guide for beginners. You do not need any
other script from this repository to follow it.

The same pattern can be used with any server that exposes these v1 services.
Fluent is the most common example, so this guide uses Fluent as the server.

## 1. What this package gives you

The `ansys-api-fluent` package already contains the generated Python files for
the Fluent gRPC APIs.

That means:

- You do not need to run `protoc` yourself.
- You import the generated v1 modules directly from `ansys.api.fluent.v1`.
- You can start building a client immediately.

Typical imports look like this:

```python
from ansys.api.fluent.v1 import field_data_pb2
from ansys.api.fluent.v1 import field_data_pb2_grpc
from ansys.api.fluent.v1 import health_pb2
from ansys.api.fluent.v1 import health_pb2_grpc
```

In general:

- `*_pb2.py` contains request and response message types
- `*_pb2_grpc.py` contains service stub classes

This guide stays focused on v1 only.

## 2. What you need before you start

You need:

- Python 3.10 or later
- A running v1 gRPC server
- The server IP address or host name
- The server port
- The server password

If you are using Fluent as the server, that means you need a running Fluent
instance with gRPC enabled and you need its host, port, and password.

For remote or secured deployments, you may need TLS certificates and 
`grpc.secure_channel()` instead.

## 3. Install the package

Install the package in your Python environment:

```bash
pip install ansys-api-fluent
```

If you want to work in a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install ansys-api-fluent
```

## 4. The basic idea

Most v1 gRPC clients follow the same simple steps:

1. Create a gRPC channel to the server.
2. Create a stub for the service you want to use.
3. Create a request message.
4. Call the RPC.
5. Read the response.

With Fluent, you usually also send the server password as gRPC metadata on each
call:

```python
metadata = [("password", password)]
```

This guide shows that pattern in a complete working example.

## 5. Complete example

The script below does all of the following in one place:

- Connects to a Fluent v1 server
- Runs a health check
- Lists available surfaces
- Lists available scalar fields
- Chooses the first surface and first scalar field
- Gets the value range for that field on that surface
- Streams scalar field values with `GetFields`
- Prints a short summary

```python
from __future__ import annotations

import grpc

from ansys.api.fluent.v1 import field_data_pb2
from ansys.api.fluent.v1 import field_data_pb2_grpc
from ansys.api.fluent.v1 import health_pb2
from ansys.api.fluent.v1 import health_pb2_grpc


HOST = "127.0.0.1"
PORT = 50051
PASSWORD = "your-fluent-password"
NODE_VALUES = True


def data_location(node_values: bool) -> field_data_pb2.DataLocation:
    return (
        field_data_pb2.DataLocation.DATA_LOCATION_NODES
        if node_values
        else field_data_pb2.DataLocation.DATA_LOCATION_ELEMENTS
    )


def main() -> None:
    channel = grpc.insecure_channel(f"{HOST}:{PORT}")
    metadata = [("password", PASSWORD)]

    health_stub = health_pb2_grpc.HealthStub(channel)
    field_stub = field_data_pb2_grpc.FieldDataStub(channel)

    try:
        print(f"Connecting to {HOST}:{PORT} ...")

        health_response = health_stub.Check(
            health_pb2.HealthCheckRequest(),
            metadata=metadata,
            timeout=5.0,
        )
        print(f"Health check status: {health_response.status}")

        surfaces_response = field_stub.GetSurfacesInfo(
            field_data_pb2.GetSurfacesInfoRequest(),
            metadata=metadata,
            timeout=10.0,
        )

        surfaces: list[tuple[int, str]] = []
        for info in surfaces_response.surface_info:
            for surface_id in info.surface_ids:
                surfaces.append((surface_id.id, info.surface_name or "<unnamed>"))

        if not surfaces:
            raise RuntimeError("The server returned no surfaces.")

        print("Available surfaces (first 10):")
        for surface_id, surface_name in surfaces[:10]:
            print(f"  id={surface_id} name={surface_name}")

        chosen_surface_id, chosen_surface_name = surfaces[0]
        print(
            "Using surface: "
            f"id={chosen_surface_id} name={chosen_surface_name}"
        )

        fields_response = field_stub.GetFieldsInfo(
            field_data_pb2.GetFieldsInfoRequest(),
            metadata=metadata,
            timeout=10.0,
        )

        if not fields_response.field_info:
            raise RuntimeError("The server returned no scalar fields.")

        print("Available scalar fields (first 10):")
        for item in fields_response.field_info[:10]:
            print(
                "  "
                f"solver_name={item.solver_name} "
                f"display_name={item.display_name}"
            )

        chosen_field = fields_response.field_info[0].solver_name
        print(f"Using scalar field: {chosen_field}")

        range_request = field_data_pb2.GetRangeRequest(
            field_name=chosen_field,
            surface_ids=[field_data_pb2.SurfaceId(id=chosen_surface_id)],
            node_value=NODE_VALUES,
        )
        range_response = field_stub.GetRange(
            range_request,
            metadata=metadata,
            timeout=20.0,
        )
        print(
            "Field range: "
            f"min={range_response.minimum:.6g} "
            f"max={range_response.maximum:.6g}"
        )

        fields_request = field_data_pb2.GetFieldsRequest(
            provide_bytes_stream=False,
            chunk_size=256 * 1024,
            scalar_field_requests=[
                field_data_pb2.ScalarFieldRequest(
                    surface_id=chosen_surface_id,
                    scalar_field_name=chosen_field,
                    data_location=data_location(NODE_VALUES),
                    provide_boundary_values=False,
                )
            ],
        )

        value_count = 0
        local_min: float | None = None
        local_max: float | None = None
        payload_info_count = 0

        for chunk in field_stub.GetFields(
            fields_request,
            metadata=metadata,
            timeout=120.0,
        ):
            chunk_name = chunk.WhichOneof("chunk")

            if chunk_name == "payload_info":
                payload_info_count += 1
                continue

            if chunk_name == "double_payload":
                values = list(chunk.double_payload.payloads)
            elif chunk_name == "float_payload":
                values = [float(value) for value in chunk.float_payload.payloads]
            elif chunk_name == "int_payload":
                values = [float(value) for value in chunk.int_payload.payloads]
            elif chunk_name == "long_payload":
                values = [float(value) for value in chunk.long_payload.payloads]
            else:
                continue

            if not values:
                continue

            value_count += len(values)
            chunk_min = min(values)
            chunk_max = max(values)
            local_min = chunk_min if local_min is None else min(local_min, chunk_min)
            local_max = chunk_max if local_max is None else max(local_max, chunk_max)

        print("\nStream summary")
        print(f"  Surface id: {chosen_surface_id}")
        print(f"  Surface name: {chosen_surface_name}")
        print(f"  Scalar field: {chosen_field}")
        print(f"  Values streamed: {value_count}")
        print(f"  Payload info chunks: {payload_info_count}")
        print(f"  Local min/max from stream: {local_min} / {local_max}")

    except grpc.RpcError as err:
        print(f"gRPC error: code={err.code()} details={err.details()}")
        raise
    finally:
        channel.close()


if __name__ == "__main__":
    main()
```

## 6. How to use the example

1. Copy the script into a Python file.
2. Set `HOST`, `PORT`, and `PASSWORD` for your server.
3. Run the script.

```bash
python your_client.py
```

If you are connecting to Fluent, use the Fluent server IP, port, and password.

## 7. What the example is doing

The script is intentionally simple. It teaches the core ideas that a beginner
needs first.

### 7.1 Connect to the server

This line creates a channel to the server:

```python
channel = grpc.insecure_channel(f"{HOST}:{PORT}")
```

For local development, this is often enough.

### 7.2 Send the password as metadata

This line prepares the password that Fluent expects on each RPC call:

```python
metadata = [("password", PASSWORD)]
```

The metadata is then passed into service calls like this:

```python
response = stub.SomeRpc(request, metadata=metadata, timeout=10.0)
```

### 7.3 Create service stubs

Stubs are the Python objects you use to call server methods:

```python
health_stub = health_pb2_grpc.HealthStub(channel)
field_stub = field_data_pb2_grpc.FieldDataStub(channel)
```

### 7.4 Run a health check

This is the simplest useful call. It tells you whether the server is reachable
and responding:

```python
health_response = health_stub.Check(
    health_pb2.HealthCheckRequest(service=""),
    metadata=metadata,
    timeout=5.0,
)
```

If this call fails, fix the connection details before trying more advanced
services.

### 7.5 Discover surfaces and fields

These two calls ask the server what field data can be requested:

```python
surfaces_response = field_stub.GetSurfacesInfo(
    field_data_pb2.GetSurfacesInfoRequest(),
    metadata=metadata,
    timeout=10.0,
)

fields_response = field_stub.GetFieldsInfo(
    field_data_pb2.GetFieldsInfoRequest(),
    metadata=metadata,
    timeout=10.0,
)
```

This is a good beginner workflow because you do not need to guess valid surface
IDs or field names.

### 7.6 Get the field range

Before streaming all values, the script asks for the minimum and maximum:

```python
range_request = field_data_pb2.GetRangeRequest(
    field_name=chosen_field,
    surface_ids=[field_data_pb2.SurfaceId(id=chosen_surface_id)],
    node_value=NODE_VALUES,
)
range_response = field_stub.GetRange(
    range_request,
    metadata=metadata,
    timeout=20.0,
)
```

This is useful when you want a quick summary before processing a larger stream.

### 7.7 Stream scalar field values

The `GetFields` RPC returns a stream of chunks. The script reads those chunks,
extracts numeric payloads, and builds a simple summary.

This is the most important beginner idea for streamed RPCs:

- build a request
- iterate over the returned stream
- process one chunk at a time

## 8. How to make the script your own

Once the basic script works, the most common changes are simple.

### 8.1 Pick a different surface

Instead of using the first surface in the returned list, choose the one whose
ID or name you want.

### 8.2 Pick a different field

Instead of using the first scalar field, set `chosen_field` to the solver field
name you want to request.

### 8.3 Use element values instead of node values

Set:

```python
NODE_VALUES = False
```

### 8.4 Request more services

The same pattern works for other v1 services in this package:

1. import the `*_pb2` and `*_pb2_grpc` modules
2. create a stub
3. build a request
4. call the RPC with `metadata=metadata`
5. read the response

## 9. Common errors

### Import error

Cause:

- `ansys-api-fluent` is not installed in the Python environment you are using

Fix:

- install the package in that same environment

### `UNAVAILABLE`

Cause:

- wrong host or port
- server is not running
- network problem
- secure versus insecure channel mismatch

Fix:

- verify the server address and port
- confirm the server is running
- check whether your server requires a secure channel

### Authentication or permission failure

Cause:

- wrong password
- password metadata was not sent

Fix:

- verify the password
- make sure each RPC includes `metadata=[("password", PASSWORD)]`

### `DEADLINE_EXCEEDED`

Cause:

- the timeout is too short

Fix:

- increase the timeout, especially for larger field data requests

## 10. Summary

If you are new to this package, keep the workflow simple:

1. install `ansys-api-fluent`
2. connect to your v1 server
3. send the password as metadata
4. verify the connection with `Health.Check`
5. query surfaces and fields with `FieldData`
6. request the data you need

That is the core of building a simple Python RPC client with Fluent v1.
