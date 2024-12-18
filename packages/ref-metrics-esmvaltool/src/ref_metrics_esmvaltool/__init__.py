"""
Rapid evaluating CMIP data with ESMValTool.
"""

import importlib.metadata

from ref_core.providers import MetricsProvider

from ref_metrics_esmvaltool.example import GlobalMeanTimeseries

__version__ = importlib.metadata.version("ref_metrics_esmvaltool")
__core_version__ = importlib.metadata.version("ref_core")

# Initialise the metrics manager and register the example metric
provider = MetricsProvider("ESMValTool", __version__)
provider.register(GlobalMeanTimeseries())
