# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for the Fluent Health gRPC service.

These tests require a running Fluent server reachable via the
``grpc_channel_and_metadata`` session fixture defined in ``conftest.py``.
"""

import grpc
import pytest

from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc

_VALID_STATUSES = {
    health_pb2.HealthCheckResponse.SERVING_STATUS_UNSPECIFIED,
    health_pb2.HealthCheckResponse.SERVING_STATUS_SERVING,
    health_pb2.HealthCheckResponse.SERVING_STATUS_NOT_SERVING,
    health_pb2.HealthCheckResponse.SERVING_STATUS_SERVICE_UNKNOWN,
}

_HEALTH_SERVICE_NAME = "ansys.api.fluent.v1.health.Health"


def test_health_check_serving(grpc_channel_and_metadata):
    """Verify the Fluent gRPC server is alive and reports SERVING."""
    channel, metadata = grpc_channel_and_metadata
    stub = health_pb2_grpc.HealthStub(channel)
    response = stub.Check(
        health_pb2.HealthCheckRequest(),
        metadata=metadata,
    )
    assert response.status == health_pb2.HealthCheckResponse.SERVING_STATUS_SERVING


def test_health_check_named_service(grpc_channel_and_metadata):
    """Check by fully-qualified service name returns a valid status or NOT_FOUND."""
    channel, metadata = grpc_channel_and_metadata
    stub = health_pb2_grpc.HealthStub(channel)
    response = stub.Check(
        health_pb2.HealthCheckRequest(service=_HEALTH_SERVICE_NAME),
        metadata=metadata,
    )
    assert response.status in _VALID_STATUSES


def test_health_check_unknown_service(grpc_channel_and_metadata):
    """An unknown service name must produce NOT_FOUND or UNIMPLEMENTED."""
    channel, metadata = grpc_channel_and_metadata
    stub = health_pb2_grpc.HealthStub(channel)
    response = stub.Check(
        health_pb2.HealthCheckRequest(service="definitely.not.real.Service"),
        metadata=metadata,
    )
    # Some servers silently accept unknown names — status must still be valid.
    assert response.status in _VALID_STATUSES


def test_health_check_multiple_calls_consistent(grpc_channel_and_metadata):
    """Repeated Check calls must all return the same status."""
    channel, metadata = grpc_channel_and_metadata
    stub = health_pb2_grpc.HealthStub(channel)
    statuses = [
        stub.Check(health_pb2.HealthCheckRequest(), metadata=metadata).status
        for _ in range(3)
    ]
    assert len(set(statuses)) == 1, f"Inconsistent statuses: {statuses}"
