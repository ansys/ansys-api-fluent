# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the ansys-api-fluent package to the path
sys.path.insert(0, os.path.abspath(".."))
# Make the local Sphinx extensions importable
sys.path.insert(0, os.path.abspath("_ext"))

from ansys_sphinx_theme import ansys_favicon

project = "ansys-api-fluent"
copyright = "(c) 2026 ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
cname = os.getenv("DOCUMENTATION_CNAME", "nocname.com")

from ansys.api.fluent._version import __version__

release = __version__
version = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_tabs.tabs",
    # Local extension: regenerates docs/source/api/_generated/*.rst from the
    # v1 .proto files at the start of every Sphinx build.
    "proto_docgen",
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
