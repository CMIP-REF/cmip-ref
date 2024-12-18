from typing import Any

import xarray
from ref_core.datasets import FacetFilter, SourceDatasetType
from ref_core.metrics import DataRequirement, Metric, MetricExecutionDefinition, MetricResult
from ruamel.yaml import YAML

from ref_metrics_esmvaltool.recipe import dataframe_to_recipe, load_recipe, run_recipe

yaml = YAML()


def format_cmec_output_bundle(dataset: xarray.Dataset) -> dict[str, Any]:
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
            dataset.attrs["source_id"]: {"global": {"tas": 0}},
        },
    }

    return cmec_output


class GlobalMeanTimeseries(Metric):
    """
    Calculate the annual mean global mean timeseries for a dataset
    """

    name = "Global Mean Timeseries"
    slug = "esmvaltool-global-mean-timeseries"

    data_requirements = (
        DataRequirement(
            source_type=SourceDatasetType.CMIP6,
            filters=(FacetFilter(facets={"variable_id": ("tas",)}),),
            # Add cell areas to the groups
            # constraints=(AddCellAreas(),),
            # Run the metric on each unique combination of model, variable, experiment, and variant
            group_by=("source_id", "variable_id", "experiment_id", "variant_label"),
        ),
    )

    def run(self, definition: MetricExecutionDefinition) -> MetricResult:
        """
        Run a metric

        Parameters
        ----------
        definition
            A description of the information needed for this execution of the metric

        Returns
        -------
        :
            The result of running the metric.
        """
        # Load recipe and clear unwanted elements
        recipe = load_recipe("examples/recipe_python.yml")
        recipe["datasets"].clear()
        recipe["diagnostics"].pop("map")
        variables = recipe["diagnostics"]["timeseries"]["variables"]
        variables.clear()

        # Prepare updated variables section in recipe.
        recipe_variables = dataframe_to_recipe(definition.metric_dataset[SourceDatasetType.CMIP6].datasets)
        for variable in recipe_variables.values():
            variable["preprocessor"] = "annual_mean_global"
            variable["caption"] = "Annual global mean {long_name} according to {dataset}."

        # Populate recipe with new variables/datasets.
        variables.update(recipe_variables)

        # Run recipe
        result_dir = run_recipe(recipe, definition)
        result = next(result_dir.glob("work/timeseries/script1/*.nc"))
        annual_mean_global_mean_timeseries = xarray.open_dataset(result)

        return MetricResult.build(definition, format_cmec_output_bundle(annual_mean_global_mean_timeseries))
