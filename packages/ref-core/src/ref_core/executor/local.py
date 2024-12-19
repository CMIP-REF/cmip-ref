from attrs import evolve
from loguru import logger

from ref.config import Config
from ref_core.metrics import Metric, MetricExecutionDefinition, MetricResult


class LocalExecutor:
    """
    Run a metric locally, in-process.

    This is mainly useful for debugging and testing.
    The production executor will run the metric in a separate process or container,
    the exact manner of which is yet to be determined.
    """

    name = "local"

    def __init__(self, config: Config | None = None):
        self.config = Config.default() if config is None else config

    def run_metric(self, metric: Metric, definition: MetricExecutionDefinition) -> MetricResult:
        """
        Run a metric in process

        Parameters
        ----------
        metric
            Metric to run
        definition
            A description of the information needed for this execution of the metric

        Returns
        -------
        :
            Results from running the metric
        """
        # TODO: This should be changed to use executor specific configuration
        definition = evolve(definition, output_directory=self.config.paths.tmp)
        definition.output_filename().mkdir(parents=True, exist_ok=True)

        try:
            return metric.run(definition=definition)
        except Exception:
            logger.exception(f"Error running metric {metric.slug}")
            return MetricResult.build_from_failure()
