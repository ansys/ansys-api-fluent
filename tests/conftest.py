"""Pytest configuration and shared fixtures for the ansys-api-fluent test suite.

A single Fluent solver process is launched once per test session and its gRPC
channel and metadata are shared with every test file via the
``grpc_channel_and_metadata`` session-scoped fixture.
"""

import pytest
import ansys.fluent.core as pyfluent


@pytest.fixture(scope="session")
def fluent_solver():
    """Launch a single Fluent solver session shared across the entire test run.

    The session is torn down (and the Fluent process exited) automatically
    after all tests have finished.
    """
    solver = pyfluent.launch_fluent(mode="solver", ui_mode="gui", cleanup_on_exit=True)
    yield solver
    solver.exit()


@pytest.fixture(scope="session")
def grpc_channel_and_metadata(fluent_solver):
    """Return the gRPC channel and metadata from the shared Fluent session.

    Yields
    ------
    tuple[grpc.Channel, list[tuple[str, str]]]
        ``(channel, metadata)`` ready for use with any generated stub class.
    """
    connection = fluent_solver._fluent_connection
    yield connection._channel, connection._metadata
