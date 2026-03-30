from __future__ import annotations

from dataclasses import dataclass

import grpc

from ansys.api.fluent.v1 import field_data_pb2
from ansys.api.fluent.v1 import field_data_pb2_grpc
from ansys.api.fluent.v1 import health_pb2
from ansys.api.fluent.v1 import health_pb2_grpc


@dataclass
class SurfaceChoice:
    id: int
    name: str


@dataclass
class FieldChoice:
    solver_name: str
    display_name: str


@dataclass
class StreamSummary:
    value_count: int
    streamed_min: float | None
    streamed_max: float | None
    payload_infos_seen: int


def create_channel(host: str, port: int) -> grpc.Channel:
    target = f"{host}:{port}"
    return grpc.insecure_channel(target)


def check_health(channel: grpc.Channel) -> None:
    health_stub = health_pb2_grpc.HealthStub(channel)
    response = health_stub.Check(health_pb2.HealthCheckRequest(service=""), timeout=5.0)
    print(f"Health status enum value: {response.status}")


def pick_surface(field_stub: field_data_pb2_grpc.FieldDataStub) -> SurfaceChoice:
    response = field_stub.GetSurfacesInfo(field_data_pb2.GetSurfacesInfoRequest(), timeout=10.0)

    candidates: list[SurfaceChoice] = []
    for info in response.surface_info:
        for sid in info.surface_ids:
            candidates.append(SurfaceChoice(id=sid.id, name=info.surface_name or "<unnamed>"))

    if not candidates:
        raise RuntimeError("No surfaces returned by GetSurfacesInfo.")

    print("Available surfaces (first 10):")
    for item in candidates[:10]:
        print(f"  id={item.id} name={item.name}")

    chosen = candidates[0]
    print(f"Using surface: id={chosen.id} name={chosen.name}")
    return chosen


def pick_scalar_field(field_stub: field_data_pb2_grpc.FieldDataStub) -> FieldChoice:
    response = field_stub.GetFieldsInfo(field_data_pb2.GetFieldsInfoRequest(), timeout=10.0)

    if not response.field_info:
        raise RuntimeError("No scalar fields returned by GetFieldsInfo.")

    print("Available scalar fields (first 10):")
    for item in response.field_info[:10]:
        print(f"  solver_name={item.solver_name} display_name={item.display_name}")

    chosen = response.field_info[0]
    result = FieldChoice(solver_name=chosen.solver_name, display_name=chosen.display_name)
    print(
        "Using scalar field: "
        f"solver_name={result.solver_name} display_name={result.display_name}"
    )
    return result


def get_scalar_range(
    field_stub: field_data_pb2_grpc.FieldDataStub,
    surface_id: int,
    scalar_solver_name: str,
    *,
    node_value: bool,
) -> tuple[float, float]:
    request = field_data_pb2.GetRangeRequest(
        field_name=scalar_solver_name,
        surface_ids=[field_data_pb2.SurfaceId(id=surface_id)],
        node_value=node_value,
    )
    response = field_stub.GetRange(request, timeout=20.0)
    return response.minimum, response.maximum


def _data_location(node_value: bool) -> field_data_pb2.DataLocation:
    return (
        field_data_pb2.DataLocation.DATA_LOCATION_NODES
        if node_value
        else field_data_pb2.DataLocation.DATA_LOCATION_ELEMENTS
    )


def stream_scalar_field_via_get_fields(
    field_stub: field_data_pb2_grpc.FieldDataStub,
    surface_id: int,
    scalar_solver_name: str,
    *,
    node_value: bool,
) -> StreamSummary:
    # This request shape mirrors pyfluent's v1 path:
    # GetFieldsRequest + ScalarFieldRequest(data_location, provide_boundary_values).
    request = field_data_pb2.GetFieldsRequest(
        provide_bytes_stream=False,
        chunk_size=256 * 1024,
        scalar_field_requests=[
            field_data_pb2.ScalarFieldRequest(
                surface_id=surface_id,
                scalar_field_name=scalar_solver_name,
                data_location=_data_location(node_value),
                provide_boundary_values=False,
            )
        ],
    )

    total_values = 0
    streamed_min: float | None = None
    streamed_max: float | None = None
    payload_infos_seen = 0

    for chunk in field_stub.GetFields(request, timeout=120.0):
        which = chunk.WhichOneof("chunk")

        if which == "payload_info":
            payload_infos_seen += 1
            continue

        if which == "double_payload":
            values = list(chunk.double_payload.payloads)
        elif which == "float_payload":
            values = [float(v) for v in chunk.float_payload.payloads]
        elif which == "int_payload":
            values = [float(v) for v in chunk.int_payload.payloads]
        elif which == "long_payload":
            values = [float(v) for v in chunk.long_payload.payloads]
        else:
            # Bytes payload can appear when provide_bytes_stream=True.
            continue

        if values:
            total_values += len(values)
            local_min = min(values)
            local_max = max(values)
            streamed_min = local_min if streamed_min is None else min(streamed_min, local_min)
            streamed_max = local_max if streamed_max is None else max(streamed_max, local_max)

    return StreamSummary(
        value_count=total_values,
        streamed_min=streamed_min,
        streamed_max=streamed_max,
        payload_infos_seen=payload_infos_seen,
    )


def main() -> None:
    host = "127.0.0.1"
    port = 50051
    node_value = True

    channel = create_channel(host=host, port=port)
    field_stub = field_data_pb2_grpc.FieldDataStub(channel)

    try:
        check_health(channel)

        surface = pick_surface(field_stub)
        scalar_field = pick_scalar_field(field_stub)

        rmin, rmax = get_scalar_range(
            field_stub,
            surface.id,
            scalar_field.solver_name,
            node_value=node_value,
        )
        print(f"GetRange => min={rmin:.6g}, max={rmax:.6g}")

        stream_summary = stream_scalar_field_via_get_fields(
            field_stub,
            surface.id,
            scalar_field.solver_name,
            node_value=node_value,
        )

        print("\nStream summary")
        print(f"  Surface id: {surface.id}")
        print(f"  Surface name: {surface.name}")
        print(f"  Scalar field: {scalar_field.solver_name}")
        print(f"  Values streamed: {stream_summary.value_count}")
        print(f"  Payload info chunks: {stream_summary.payload_infos_seen}")
        print(
            "  Stream local min/max: "
            f"{stream_summary.streamed_min} / {stream_summary.streamed_max}"
        )

    except grpc.RpcError as err:
        print(f"gRPC error: code={err.code()} details={err.details()}")
        raise


if __name__ == "__main__":
    main()
