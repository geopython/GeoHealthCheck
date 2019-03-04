Themes for GHC Docs
===================

Background, see: [issue #239](https://github.com/geopython/GeoHealthCheck/issues/239).

Currently the [Read The DOcs Sphinx Theme](https://sphinx-rtd-theme.readthedocs.io/en/stable/) is used.

Although this theme is preferably installed via `pip install sphinx_rtd_theme`, we found that it
installed around 9.5 MB of static files, most of which were (fontawesome, Lato?) fonts.
The GHC generated docs tree would grow from 2.5MB to over 12MB just for this theme...

So the alternative installation using a release download is used, 
and [installation as described here](https://sphinx-rtd-theme.readthedocs.io/en/stable/installing.html#via-git-or-download).

In order to know what is installed and for upgrades, the version number is included under the `_themes` dir.

To install or upgrade the RTD theme, follow these steps:

* download a release from [RTD Theme Releases](https://github.com/rtfd/sphinx_rtd_theme/releases)
* unpack
* copy the subtree `sphinx_rtd_theme/sphinx_rtd_theme` (the generated files) under `_themes`
* rename the copied dir to `_themes/sphinx_rtd_theme_<version_number>` e.g. `_themes/sphinx_rtd_theme_0.4.3`
* adapt [conf.py](../conf.py) line 106: e.g. `html_theme = "sphinx_rtd_theme_0.4.3"`
