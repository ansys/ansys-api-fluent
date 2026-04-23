# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the ansys-api-fluent package to the path
sys.path.insert(0, os.path.abspath(".."))

project = "ansys-api-fluent"
copyright = "2026 ANSYS, Inc."
author = "ANSYS, Inc."

from ansys.api.fluent._version import __version__

release = __version__
version = ".".join(__version__.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_logo = None
html_favicon = None

html_theme_options = {
    "navigation_depth": 5,
    "collapse_navigation": True,
    "sticky_navigation": True,
    "sticky_navigation_offset": 120,
    "prev_next_buttons_location": "bottom",
    "display_version": True,
    "includehidden": True,
    "display_github": True,
    "github_url": "https://github.com/ansys/ansys-api-fluent",
    "github_user": "ansys",
    "github_repo": "ansys-api-fluent",
    "github_version": "main",
    "conf_py_path": "/docs/",
}

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

# JSON schema for Sphinx
json_schema_draft = "2020-12"

# Source file quality indicator
nitpick_ignore = []

# Suppress warnings
suppress_warnings = [
    "myst.header_anchor",
]
