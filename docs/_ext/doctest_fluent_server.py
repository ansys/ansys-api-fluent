"""Sphinx extension: start a live Fluent server once for the doctest build.

A solver session (with the mixing_elbow case loaded) and a mesher session are
launched during ``builder-inited`` and torn down after ``build-finished``.
All doctest groups access the same sessions via :func:`get_connections`.
"""

from __future__ import annotations

_connections: dict = {}


def get_connections() -> dict:
    """Return the shared channel/metadata dict populated at build start.

    Keys: ``solver_channel``, ``solver_metadata``,
    ``mesher_channel``, ``mesher_metadata``.
    Returns an empty dict when the server has not been started (e.g. during a
    plain ``make html`` build).
    """
    return _connections


def _start(app) -> None:
    if app.builder.name != "doctest":
        return

    try:
        import ansys.fluent.core as pyfluent
        from ansys.fluent.core import examples
        from ansys.fluent.core.docker.utils import get_grpc_launcher_args_for_gh_runs
    except ImportError as exc:
        import warnings

        warnings.warn(
            f"doctest_fluent_server: ansys-fluent-core not importable ({exc}); "
            "server-dependent doctests will be skipped.",
            stacklevel=2,
        )
        return

    try:
        args = get_grpc_launcher_args_for_gh_runs()

        # Ensure pyfluent can locate the Fluent installation.
        import os as _os

        _fluent_root = _os.environ.get("FLUENT_ROOT", "/home/ANSYSDev/v271")
        _fluent_bin = f"{_fluent_root}/fluent/bin/fluent"
        _os.environ.setdefault("AWP_ROOT271", _fluent_root)

        # Fluent's cortex binary requires several bundled shared libraries that
        # are not on the system library path.  Prepend them so the dynamic
        # linker can resolve them without modifying the system configuration.
        _fluent_lib_dirs = [
            f"{_fluent_root}/fluent/lib/lnamd64",
            f"{_fluent_root}/fluent/lib/lnamd64/Qt/lib",
            f"{_fluent_root}/commonfiles/CFX/tools/boost-1.87.0/1_87_0/lib/Release",
            f"{_fluent_root}/commonfiles/CPython/3_13/linx64/Release/python/lib",
        ]
        _existing = _os.environ.get("LD_LIBRARY_PATH", "")
        _os.environ["LD_LIBRARY_PATH"] = ":".join(_fluent_lib_dirs) + (
            f":{_existing}" if _existing else ""
        )

        # --- solver ---
        solver = pyfluent.launch_fluent(
            mode="solver", cleanup_on_exit=True, fluent_path=_fluent_bin, **args
        )
        import_file = examples.download_file(
            "mixing_elbow.cas.h5", "pyfluent/mixing_elbow"
        )
        examples.download_file("mixing_elbow.dat.h5", "pyfluent/mixing_elbow")
        solver.settings.file.read_case_data(file_name=import_file)
        # Initialize the solver so iterate() calls in doctests are stable.
        solver.settings.solution.initialization.hybrid_initialize()

        # Extend idle timeout so the session survives the full doctest run.
        from datetime import timedelta

        from ansys.api.fluent.v1 import (
            application_runtime_pb2,
            application_runtime_pb2_grpc,
        )

        _sc = solver._fluent_connection
        _ar_stub = application_runtime_pb2_grpc.ApplicationRuntimeStub(_sc._channel)
        _ar_stub.SetIdleTimeout(
            application_runtime_pb2.SetIdleTimeoutRequest(
                timeout=timedelta(seconds=7200)
            ),
            metadata=list(_sc._metadata),
        )

        # --- mesher ---
        mesher = pyfluent.launch_fluent(
            mode="meshing", cleanup_on_exit=True, fluent_path=_fluent_bin, **args
        )
        mesher.watertight()

        sc = solver._fluent_connection
        mc = mesher._fluent_connection

        _connections.update(
            solver=solver,
            mesher=mesher,
            solver_channel=sc._channel,
            solver_metadata=list(sc._metadata),
            mesher_channel=mc._channel,
            mesher_metadata=list(mc._metadata),
        )

        # Keep both sessions alive with periodic health pings.
        import threading

        from ansys.api.fluent.v1 import health_pb2
        from ansys.api.fluent.v1 import health_pb2_grpc as _h_grpc

        _stop_evt = threading.Event()
        _connections["_stop_event"] = _stop_evt

        def _keepalive():
            pairs = [
                (sc._channel, list(sc._metadata)),
                (mc._channel, list(mc._metadata)),
            ]
            while not _stop_evt.wait(timeout=2):
                for ch, meta in pairs:
                    try:
                        _h_grpc.HealthStub(ch).Check(
                            health_pb2.HealthCheckRequest(),
                            metadata=meta,
                            timeout=2,
                        )
                    except Exception:
                        pass

        threading.Thread(
            target=_keepalive, daemon=True, name="fluent-keepalive"
        ).start()
    except Exception as exc:
        import warnings

        warnings.warn(
            f"doctest_fluent_server: failed to start Fluent server ({exc}); "
            "server-dependent doctests will be skipped.",
            stacklevel=2,
        )


def _stop(app, exception) -> None:
    stop_evt = _connections.get("_stop_event")
    if stop_evt is not None:
        stop_evt.set()
    for key in ("solver", "mesher"):
        session = _connections.get(key)
        if session is not None:
            try:
                session.exit()
            except Exception:
                pass


def setup(app):
    app.connect("builder-inited", _start)
    app.connect("build-finished", _stop)
    return {"version": "0.1", "parallel_read_safe": False}
