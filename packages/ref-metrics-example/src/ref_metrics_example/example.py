import json

from ref_core.metrics import MetricResult
from ref_core.providers import Configuration


class ExampleMetric:
    """
    Example metric that does nothing but count the number of times it has been run.
    """

    name = "example"

    def __init__(self):
        self._count = 0

    def run(self, configuration: Configuration) -> MetricResult:
        """
        Run a metric

        Parameters
        ----------
        configuration

        Returns
        -------
        :
            The result of running the metric.
        """
        self._count += 1

        with open(configuration.output_directory / "output.json", "w") as fh:
            json.dump(({"count": self._count}), fh)

        return MetricResult(
            output_bundle=configuration.output_directory / "output.json",
            successful=True,
        )
