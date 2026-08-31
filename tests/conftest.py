# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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