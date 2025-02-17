from typing import Protocol, runtime_checkable

from cmip_ref.models import MetricExecutionResult
from cmip_ref_core.metrics import Metric, MetricExecutionDefinition
from cmip_ref_core.providers import MetricsProvider


@runtime_checkable
class Executor(Protocol):
    """
    An executor is responsible for running a metric asynchronously

    The metric may be run locally in the same process or in a separate process or container.

    Notes
    -----
    This is an extremely basic interface and will be expanded in the future, as we figure out
    our requirements.
    """

    name: str

    def run_metric(
        self,
        provider: MetricsProvider,
        metric: Metric,
        definition: MetricExecutionDefinition,
        metric_execution_result: MetricExecutionResult | None = None,
    ) -> None:
        """
        Execute a metric

        No results are returned from this method,
        as the execution may be performed asynchrounusly so results may not be immediately available.

        /// admonition | Note
        In future, we may return a `Future` object that can be used to retrieve the result,
        but that requires some additional work to implement.
        ///

        Parameters
        ----------
        provider
            Provider of the metric
        metric
            Metric to run
        definition
            Definition of the information needed to execute a metric

            This definition describes which datasets are required to run the metric and where
            the output should be stored.
        metric_execution_result
            Result of the metric execution

            This is a database object that contains the results of the execution.
            If provided, it will be updated with the results of the execution.
            This may happen asynchronously, so the results may not be immediately available.

        Returns
        -------
        :
            Results from running the metric
        """
        ...

    def join(self, timeout: float) -> None:
        """
        Wait for all metrics to finish executing

        If the timeout is reached, the method will return and raise an exception.

        Parameters
        ----------
        timeout
            Maximum time to wait for all metrics to finish executing in seconds

        Raises
        ------
        TimeoutError
            If the timeout is reached
        """
