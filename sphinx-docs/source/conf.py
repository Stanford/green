# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'stanford-green'
copyright = '2024, Adam H. Lewenberg'
author = 'Adam H. Lewenberg'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
'sphinx.ext.autodoc',
'sphinx_markdown_builder',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

#html_theme_options = {
#    # Disable showing the sidebar. Defaults to 'false'
#    'nosidebar': True,
#}

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath('..')))
