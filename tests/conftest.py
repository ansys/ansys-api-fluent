"""Pytest configuration and shared fixtures for the ansys-api-fluent test suite.

A single Fluent solver process is launched once per test session and its gRPC
channel and metadata are shared with every test file via the
``grpc_channel_and_metadata`` session-scoped fixture.
"""
import pytest
import ansys.fluent.core as pyfluent
from ansys.fluent.core import examples


@pytest.fixture(scope="session")
def fluent_solver():
    """Launch a single Fluent solver session shared across the entire test run.

    The session is torn down (and the Fluent process exited) automatically
    after all tests have finished.
    """
    solver = pyfluent.launch_fluent(mode="solver", cleanup_on_exit=True)
    import_filename = examples.download_file(
        "mixing_elbow.cas.h5", "pyfluent/mixing_elbow"
    )
    examples.download_file(
        "mixing_elbow.dat.h5", "pyfluent/mixing_elbow"
    )
    solver.settings.file.read_case_data(file_name=import_filename)
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


@pytest.fixture(scope="session")
def fluent_mesher():
    """Launch a single Fluent meshing session shared across the entire test run.

    The session is torn down (and the Fluent process exited) automatically
    after all tests have finished.
    """
    meshing = pyfluent.launch_fluent(mode="meshing", cleanup_on_exit=True)
    meshing.watertight()
    yield meshing
    meshing.exit()


@pytest.fixture(scope="session")
def grpc_channel_and_metadata_meshing(fluent_mesher):
    """Return the gRPC channel and metadata from the shared Fluent session.

    Yields
    ------
    tuple[grpc.Channel, list[tuple[str, str]]]
        ``(channel, metadata)`` ready for use with any generated stub class.
    """
    connection = fluent_mesher._fluent_connection
    yield connection._channel, connection._metadata