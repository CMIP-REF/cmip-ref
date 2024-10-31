import json
import pathlib
from typing import Any, Protocol, runtime_checkable

from attrs import frozen


@frozen
class Configuration:
    """
    Configuration that describes the input data sources
    """

    output_directory: pathlib.Path
    """
    Directory to write output files to
    """

    # TODO: Add more configuration options here


@frozen
class MetricResult:
    """
    The result of running a metric.

    The content of the result follows the Earth System Metrics and Diagnostics Standards
    ([EMDS](https://github.com/Earth-System-Diagnostics-Standards/EMDS/blob/main/standards.md)).
    """

    # Do we want to load a serialised version of the output bundle here or just a file path?

    output_bundle: pathlib.Path | None
    """
    Path to the output bundle file.

    The contents of this file are defined by
    [EMDS standard](https://github.com/Earth-System-Diagnostics-Standards/EMDS/blob/main/standards.md#common-output-bundle-format-)
    """
    successful: bool
    """
    Whether the metric ran successfully.
    """
    # Log info is in the output bundle file already, but is definitely useful

    @staticmethod
    def build(configuration: Configuration, cmec_output_bundle: dict[str, Any]) -> "MetricResult":
        """
        Build a MetricResult from a CMEC output bundle.

        Parameters
        ----------
        configuration
            The configuration used to run the metric.
        cmec_output_bundle
            An output bundle in the CMEC format.

            TODO: This needs a better type hint

        Returns
        -------
        :
            A prepared MetricResult object.
            The output bundle will be written to the output directory.
        """
        with open(configuration.output_directory / "output.json", "w") as file_handle:
            json.dump(cmec_output_bundle, file_handle)
        return MetricResult(
            output_bundle=configuration.output_directory / "output.json",
            successful=True,
        )


@frozen
class TriggerInfo:
    """
    The reason why the metric was run.
    """

    dataset: pathlib.Path
    """
    Path to the dataset that triggered the metric run.
    """

    # TODO:
    # Add/remove/modified?
    # dataset metadata


@runtime_checkable
class Metric(Protocol):
    """
    Interface for the calculation of a metric.

    This is a very high-level interface to provide maximum scope for the metrics packages
    to have differing assumptions.
    The configuration and output of the metric should follow the
    Earth System Metrics and Diagnostics Standards formats as much as possible.

    See (ref_example.example.ExampleMetric)[] for an example implementation.
    """

    name: str
    """
    Name of the metric being run

    This should be unique for a given provider,
    but multiple providers can implement the same metric.
    """

    # input_variable: list[VariableDefinition]
    """
    TODO: implement VariableDefinition
    Should be extend the configuration defined in EMDS

    Variables that the metric requires to run
    Any modifications to the input data will trigger a new metric calculation.
    """
    # observation_dataset: list[ObservationDatasetDefinition]
    """
    TODO: implement ObservationDatasetDefinition
    Should be extend the configuration defined in EMDS. To check with Bouwe.
    """

    def run(self, configuration: Configuration, trigger: TriggerInfo | None) -> MetricResult:
        """
        Run the metric on the given configuration.

        The implementation of this method method is left to the metrics providers.

        A CMEC-compatible package can use: TODO: Add link to CMEC metric wrapper

        Parameters
        ----------
        configuration : Configuration
            The configuration to run the metric on.
        trigger : TriggerInfo | None
            Optional information about the dataset that triggered the metric run.

        Returns
        -------
        MetricResult
            The result of running the metric.
        """
