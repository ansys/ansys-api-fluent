"""Tests for the Fluent ApplicationRuntime gRPC service (v1).

All tests share the single Fluent session started by the ``grpc_channel_and_metadata``
session fixture in ``conftest.py``.
"""

import grpc
import pytest

from ansys.api.fluent.v1 import app_utilities_pb2, app_utilities_pb2_grpc

_VALID_APP_MODES = {
    app_utilities_pb2.APP_MODE_UNSPECIFIED,
    app_utilities_pb2.APP_MODE_MESHING,
    app_utilities_pb2.APP_MODE_SOLVER,
    app_utilities_pb2.APP_MODE_SOLVER_ICING,
    app_utilities_pb2.APP_MODE_SOLVER_AERO,
}


@pytest.fixture(scope="module")
def stub(grpc_channel_and_metadata):
    channel, _ = grpc_channel_and_metadata
    return app_utilities_pb2_grpc.ApplicationRuntimeStub(channel)


def test_get_product_version_returns_response(stub, grpc_channel_and_metadata):
    """Version fields must be non-negative integers."""
    _, metadata = grpc_channel_and_metadata
    resp = stub.GetProductVersion(
        app_utilities_pb2.GetProductVersionRequest(), metadata=metadata
    )
    assert resp.major >= 27
    assert resp.minor >= 1
    assert resp.patch >= 0


def test_get_build_info_returns_response(stub, grpc_channel_and_metadata):
    """Build info response must be returned without error."""
    _, metadata = grpc_channel_and_metadata
    resp = stub.GetBuildInfo(
        app_utilities_pb2.GetBuildInfoRequest(), metadata=metadata
    )
    assert hasattr(resp, "build_time")
    assert hasattr(resp, "build_id")
    assert hasattr(resp, "vcs_revision")
    assert hasattr(resp, "vcs_branch")
    assert len(resp.build_time) > 0
    assert resp.build_id > 0
    assert len(resp.vcs_revision) > 0
    assert len(resp.vcs_branch) > 0


def test_get_controller_process_info_returns_response(stub, grpc_channel_and_metadata):
    """Controller process info must be returned or raise UNIMPLEMENTED."""
    _, metadata = grpc_channel_and_metadata
    resp = stub.GetControllerProcessInfo(
        app_utilities_pb2.GetControllerProcessInfoRequest(), metadata=metadata
    )
    assert hasattr(resp, "hostname")
    assert hasattr(resp, "process_id")
    assert hasattr(resp, "working_directory")
    assert isinstance(resp.process_id, int)


def test_get_solver_process_info_returns_response(stub, grpc_channel_and_metadata):
    """Solver process info must include hostname and a positive PID."""
    _, metadata = grpc_channel_and_metadata
    resp = stub.GetSolverProcessInfo(
        app_utilities_pb2.GetSolverProcessInfoRequest(), metadata=metadata
    )
    assert hasattr(resp, "hostname")
    assert hasattr(resp, "process_id")
    assert hasattr(resp, "working_directory")

    assert resp.process_id > 0
    assert isinstance(resp.hostname, str)
    assert len(resp.hostname) > 0


def test_get_app_mode_returns_valid_mode(stub, grpc_channel_and_metadata):
    """App mode must be one of the known enum values."""
    _, metadata = grpc_channel_and_metadata
    resp = stub.GetAppMode(
        app_utilities_pb2.GetAppModeRequest(), metadata=metadata
    )
    assert resp.app_mode in _VALID_APP_MODES
    assert resp.app_mode != app_utilities_pb2.APP_MODE_UNSPECIFIED


def test_is_beta_enabled_returns_bool(stub, grpc_channel_and_metadata):
    """IsBetaEnabled must return a boolean field."""
    _, metadata = grpc_channel_and_metadata
    resp = stub.IsBetaEnabled(
        app_utilities_pb2.IsBetaEnabledRequest(), metadata=metadata
    )
    assert isinstance(resp.is_beta_enabled, bool)


def test_enable_beta_then_is_beta_enabled(stub, grpc_channel_and_metadata):
    """After EnableBeta, IsBetaEnabled must report True."""
    _, metadata = grpc_channel_and_metadata
    stub.EnableBeta(app_utilities_pb2.EnableBetaRequest(), metadata=metadata)
    resp = stub.IsBetaEnabled(
        app_utilities_pb2.IsBetaEnabledRequest(), metadata=metadata
    )
    assert resp.is_beta_enabled is True


def test_start_stop_python_journal_in_memory(stub, grpc_channel_and_metadata):
    """Start a journal without a file name and stop it; response must be strings."""
    _, metadata = grpc_channel_and_metadata
    start_resp = stub.StartPythonJournal(
        app_utilities_pb2.StartPythonJournalRequest(), metadata=metadata
    )
    stop_resp = stub.StopPythonJournal(
        app_utilities_pb2.StopPythonJournalRequest(
            journal_id=start_resp.journal_id
            if start_resp.HasField("journal_id")
            else None
        ),
        metadata=metadata,
    )
    assert isinstance(stop_resp.journal_str, str)
