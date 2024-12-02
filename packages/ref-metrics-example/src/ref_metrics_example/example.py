from pathlib import Path
from typing import Any

import xarray as xr
from ref_core.datasets import FacetFilter, SourceDatasetType
from ref_core.metrics import DataRequirement, Metric, MetricExecutionInfo, MetricResult, TriggerInfo


def calculate_annual_mean_timeseries(dataset: Path) -> xr.Dataset:
    """
    Calculate the annual mean timeseries for a dataset.

    While this function is implemented here,
    in most cases the metric calculation will be in the underlying benchmarking package.
    How the metric is calculated is up to the provider.

    Parameters
    ----------
    dataset
        A path to a CMIP6 dataset.

        This dataset may consist of multiple data files.

    Returns
    -------
    :
        The annual mean timeseries of the dataset
    """
    input_files = dataset.glob("*.nc")

    xr_ds = xr.open_mfdataset(list(input_files), combine="by_coords", chunks=None, use_cftime=True)

    annual_mean = xr_ds.resample(time="YS").mean()
    return annual_mean.mean(dim=["lat", "lon"], keep_attrs=True)


def format_cmec_output_bundle(dataset: xr.Dataset) -> dict[str, Any]:
    """
    Create a simple CMEC output bundle for the dataset.

    Parameters
    ----------
    dataset
        Processed dataset

    Returns
    -------
        A CMEC output bundle ready to be written to disk
    """
    # TODO: Check how timeseries data are generally serialised
    cmec_output = {
        "DIMENSIONS": {
            "dimensions": {
                "source_id": {dataset.attrs["source_id"]: {}},
                "region": {"global": {}},
                "variable": {"tas": {}},
            },
            "json_structure": [
                "model",
                "region",
                "statistic",
            ],
        },
        # Is the schema tracked?
        "SCHEMA": {
            "name": "CMEC-REF",
            "package": "example",
            "version": "v1",
        },
        "RESULTS": {
            dataset.attrs["source_id"]: {"global": {"tas": ""}},
        },
    }

    return cmec_output


class GlobalMeanTimeseries(Metric):
    """
    Calculate the annual mean global mean timeseries for a dataset
    """

    name = "global_mean_timeseries"

    data_requirements = (
        DataRequirement(
            source_type=SourceDatasetType.CMIP6,
            filters=(
                FacetFilter(facets={"variable_id": ("tas", "rsut")}),
                # Ignore some experiments because they are not relevant
                FacetFilter(facets={"experiment_id": ("1pctCO2-*", "hist-*")}, keep=False),
            ),
            # Add cell areas to the groups
            # constraints=(AddCellAreas(),),
            # Run the metric on each unique combination of model, variable, experiment, and variant
            group_by=("model_id", "variable_id", "experiment_id", "variant_label"),
        ),
    )

    def run(self, metric_info: MetricExecutionInfo, trigger: TriggerInfo | None) -> MetricResult:
        """
        Run a metric

        Parameters
        ----------
        trigger
            Trigger for what caused the metric to be executed.

        metric_info
            Configuration object

        Returns
        -------
        :
            The result of running the metric.
        """
        if trigger is None:
            # TODO: This should probably raise an exception
            return MetricResult(
                output_bundle=metric_info.output_fragment / "output.json",
                successful=False,
            )

        # This is where one would hook into however they want to run
        # their benchmarking packages.
        # cmec-driver, python calls, subprocess calls all would work
        annual_mean_global_mean_timeseries = calculate_annual_mean_timeseries(trigger.dataset)

        return MetricResult.build(metric_info, format_cmec_output_bundle(annual_mean_global_mean_timeseries))
