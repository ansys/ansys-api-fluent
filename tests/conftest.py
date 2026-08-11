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

"""Pytest configuration and shared fixtures for the ansys-api-fluent test suite.

A single Fluent solver process is launched once per test session and its gRPC
channel and metadata are shared with every test file via the
``grpc_channel_and_metadata`` session-scoped fixture.
"""
import pytest
import ansys.fluent.core as pyfluent
from ansys.fluent.core import examples
from ansys.fluent.core.docker.utils import get_grpc_launcher_args_for_gh_runs


@pytest.fixture(scope="module")
def fluent_solver():
    """Launch a single Fluent solver session shared across the entire test run.

    The session is torn down (and the Fluent process exited) automatically
    after all tests have finished.
    """
    solver = pyfluent.launch_fluent(mode="solver", cleanup_on_exit=True, **get_grpc_launcher_args_for_gh_runs())
    import_filename = examples.download_file(
        "mixing_elbow.cas.h5", "pyfluent/mixing_elbow"
    )
    examples.download_file(
        "mixing_elbow.dat.h5", "pyfluent/mixing_elbow"
    )
    solver.settings.file.read_case_data(file_name=import_filename)
    yield solver
    solver.exit()


@pytest.fixture(scope="module")
def grpc_channel_and_metadata(fluent_solver):
    """Return the gRPC channel and metadata from the shared Fluent session.

    Yields
    ------
    tuple[grpc.Channel, list[tuple[str, str]]]
        ``(channel, metadata)`` ready for use with any generated stub class.
    """
    connection = fluent_solver._fluent_connection
    yield connection._channel, connection._metadata


@pytest.fixture(scope="module")
def fluent_mesher():
    """Launch a single Fluent meshing session shared across the entire test run.

    The session is torn down (and the Fluent process exited) automatically
    after all tests have finished.
    """
    meshing = pyfluent.launch_fluent(mode="meshing", cleanup_on_exit=True, **get_grpc_launcher_args_for_gh_runs())
    meshing.watertight()
    yield meshing
    meshing.exit()


@pytest.fixture(scope="module")
def grpc_channel_and_metadata_meshing(fluent_mesher):
    """Return the gRPC channel and metadata from the shared Fluent session.

    Yields
    ------
    tuple[grpc.Channel, list[tuple[str, str]]]
        ``(channel, metadata)`` ready for use with any generated stub class.
    """
    connection = fluent_mesher._fluent_connection
    yield connection._channel, connection._metadata