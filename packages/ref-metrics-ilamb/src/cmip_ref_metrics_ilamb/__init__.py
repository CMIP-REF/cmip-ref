"""
Rapid evaluating CMIP data
"""

import importlib.metadata
import importlib.resources

import yaml

from cmip_ref_core.providers import MetricsProvider
from cmip_ref_metrics_ilamb.example import GlobalMeanTimeseries
from cmip_ref_metrics_ilamb.standard import ILAMBStandard

__version__ = importlib.metadata.version("cmip_ref_metrics_ilamb")

# Initialise the metrics manager and register the example metric
provider = MetricsProvider("ILAMB", __version__)

# Register a simple test metric
provider.register(GlobalMeanTimeseries())

# Dynamically register ILAMB metrics
for yaml_file in importlib.resources.files("cmip_ref_metrics_ilamb.configure").iterdir():
    with open(str(yaml_file)) as fin:
        metrics = yaml.safe_load(fin)
    registry_file = metrics.pop("registry")
    for metric, options in metrics.items():
        provider.register(ILAMBStandard(registry_file, options.pop("sources"), **options))
