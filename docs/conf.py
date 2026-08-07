# Configuration file for the Sphinx documentation builder.

import os
import sys

DOCS_DIR = os.path.abspath(os.path.dirname(__file__))

# Add the ansys-api-fluent package to the path
sys.path.insert(0, os.path.abspath(os.path.join(DOCS_DIR, "..")))
# Make the local Sphinx extensions importable
sys.path.insert(0, os.path.abspath(os.path.join(DOCS_DIR, "_ext")))

from ansys_sphinx_theme import ansys_favicon

project = "Ansys Fluent gRPC API"
copyright = "(c) 2026 ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
cname = os.getenv("DOCUMENTATION_CNAME", "nocname.com")

release = ""
version = ""

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx_copybutton",
    "sphinx_tabs.tabs",
    # Local extension: regenerates docs/source/api/_generated/*.rst from the
    # v1 .proto files at the start of every Sphinx build.
    "proto_docgen",
    # Local extension: launches a live Fluent server for doctest groups.
    "doctest_fluent_server",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    # Auto-generated proto reference fragments are consumed via `.. include::`
    # from the hand-written pages — they should not be rendered as standalone
    # documents.
    "api/_generated/**",
]

html_theme = "ansys_sphinx_theme"
html_title = project
html_static_path = ["source/_static"]
html_favicon = ansys_favicon

html_theme_options = {
    "github_url": "https://github.com/ansys/ansys-api-fluent",
    "show_prev_next": False,
    "show_breadcrumbs": True,
    "additional_breadcrumbs": [
        ("PyAnsys", "https://docs.pyansys.com/"),
    ],
    "navigation_depth": 5,
    "collapse_navigation": True,
}


copybutton_prompt_text = r">>> ?|\.\.\. "
copybutton_prompt_is_regexp = True

# ---------------------------------------------------------------------------
# Doctest
# ---------------------------------------------------------------------------

# Executed once before every test group.  Pulls the shared server connections
# started by the doctest_fluent_server extension into the group namespace.
doctest_global_setup = """\
import warnings

from doctest_fluent_server import get_connections as _get_connections
_c = _get_connections()

warnings.simplefilter("error")  # warnings as errors

_solver_channel  = _c.get("solver_channel")
_solver_metadata = _c.get("solver_metadata")
_mesher_channel  = _c.get("mesher_channel")
_mesher_metadata = _c.get("mesher_metadata")
# Ping each session to reset idle timers between test groups.
if _solver_channel is not None:
    from ansys.api.fluent.v1 import health_pb2, health_pb2_grpc as _h_grpc
    _hs = _h_grpc.HealthStub(_solver_channel)
    try:
        _hs.Check(health_pb2.HealthCheckRequest(), metadata=_solver_metadata, timeout=5)
    except Exception:
        pass
if _mesher_channel is not None:
    _hm = _h_grpc.HealthStub(_mesher_channel)
    try:
        _hm.Check(health_pb2.HealthCheckRequest(), metadata=_mesher_metadata, timeout=5)
    except Exception:
        pass
"""

# Intersphinx mappings
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# Autodoc options
autodoc_default_options = {
    "members": False,
    "undoc-members": False,
}

# LaTeX configuration
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
}

suppress_warnings = [
    "myst.header_anchor",
    "misc.copy_overwrite",
]

source_encoding = "utf-8"
