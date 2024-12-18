from __future__ import annotations

import importlib.resources
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pooch  # type: ignore[import-untyped]
from ref_core.datasets import SourceDatasetType
from ref_core.metrics import MetricExecutionDefinition
from ruamel.yaml import YAML

if TYPE_CHECKING:
    import pandas as pd

yaml = YAML()

FACETS = {
    "CMIP6": {
        "dataset": "source_id",
        "ensemble": "member_id",
        "exp": "experiment_id",
        "grid": "grid_label",
        "mip": "table_id",
        "short_name": "variable_id",
    },
}


def as_isodate(timestamp: pd.Timestamp) -> str:
    """Format a timestamp as an ISO 8601 datetime.

    For example, '2014-12-16 12:00:00' will be formatted as '20141216T120000'.

    Parameters
    ----------
    timestamp
        The timestamp to format.

    """
    return str(timestamp).replace(" ", "T").replace("-", "").replace(":", "")


def as_timerange(group: pd.DataFrame) -> str | None:
    """Format the timeranges from a dataframe as an ESMValTool timerange.

    Parameters
    ----------
    group
        The dataframe describing a single dataset.

    Returns
    -------
        A timerange.
    """
    start_times = group.start_time.dropna()
    if start_times.empty:
        return None
    end_times = group.end_time.dropna()
    if end_times.empty:
        return None
    return f"{as_isodate(start_times.min())}/{as_isodate(end_times.max())}"


def as_facets(
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Convert a group from the datasets dataframe to ESMValTool facets.

    Parameters
    ----------
    group:
        A group of datasets representing a single instance_id.

    Returns
    -------
        A :obj:`dict` containing facet-value pairs.

    """
    facets = {}
    first_row = group.iloc[0]
    project = first_row.instance_id.split(".", 2)[0]
    facets["project"] = project
    for esmvaltool_name, ref_name in FACETS[project].items():
        facets[esmvaltool_name] = getattr(first_row, ref_name)
    timerange = as_timerange(group)
    if timerange is not None:
        facets["timerange"] = timerange
    return facets


def dataframe_to_recipe(datasets: pd.DataFrame) -> dict[str, Any]:
    """Convert the datasets dataframe to a recipe "variables" section.

    Parameters
    ----------
    datasets
        The pandas dataframe describing the input datasets.

    Returns
    -------
        A "variables" section that can be used in an ESMValTool recipe.
    """
    variables: dict[str, Any] = {}
    # TODO: refine to make it possible to combine historical and scenario runs.
    for _, group in datasets.groupby("instance_id"):
        facets = as_facets(group)
        short_name = facets.pop("short_name")
        if short_name not in variables:
            variables[short_name] = {"additional_datasets": []}
        variables[short_name]["additional_datasets"].append(facets)
    return variables


_ESMVALTOOL_VERSION = "2.11.0"

_RECIPES = pooch.create(
    path=pooch.os_cache("ref_metrics_esmvaltool"),
    base_url="https://raw.githubusercontent.com/ESMValGroup/ESMValTool/refs/tags/v{version}/esmvaltool/recipes/",
    version=_ESMVALTOOL_VERSION,
    env="REF_METRICS_ESMVALTOOL_DATA_DIR",
)
with importlib.resources.files("ref_metrics_esmvaltool").joinpath("recipes.txt").open("rb") as _file:
    _RECIPES.load_registry(_file)


def load_recipe(recipe: str) -> dict[str, Any]:
    """Load a recipe.

    Parameters
    ----------
    recipe
        The name of an ESMValTool recipe.

    Returns
    -------
        The loaded recipe.
    """
    filename = _RECIPES.fetch(recipe)
    return yaml.load(Path(filename).read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def prepare_climate_data(datasets: pd.DataFrame, climate_data_dir: Path) -> None:
    """Symlink the input files from the Pandas dataframe into a directory tree.

    This ensures that ESMValTool can find the data and only uses the
    requested data.

    Parameters
    ----------
    datasets
        The pandas dataframe describing the input datasets.
    climate_data_dir
        The directory where ESMValTool should look for input data.
    """
    for row in datasets.itertuples():
        if not isinstance(row.instance_id, str):
            msg = f"Invalid instance_id encountered in {row}"
            raise ValueError(msg)
        if not isinstance(row.path, str):
            msg = f"Invalid path encountered in {row}"
            raise ValueError(msg)
        tgt = climate_data_dir.joinpath(*row.instance_id.split(".")) / Path(row.path).name
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.symlink_to(row.path)


def run_recipe(recipe: dict[str, Any], definition: MetricExecutionDefinition) -> Path:
    """Run an ESMValTool recipe.

    Parameters
    ----------
    recipe
        The ESMValTool recipe.
    definition
        A description of the information needed for this execution of the metric.

    """
    output_dir = definition.output_fragment

    recipe_path = output_dir / "recipe_example.yml"
    with recipe_path.open("w", encoding="utf-8") as file:
        yaml.dump(recipe, file)

    climate_data = output_dir / "climate_data"

    prepare_climate_data(
        definition.metric_dataset[SourceDatasetType.CMIP6].datasets,
        climate_data_dir=climate_data,
    )

    results_dir = output_dir / "results"
    config = {
        "drs": {
            "CMIP6": "ESGF",
        },
        "output_dir": str(results_dir),
        "rootpath": {
            "default": str(climate_data),
        },
        "search_esgf": "never",
    }
    config_dir = output_dir / "config"
    config_dir.mkdir()
    with (config_dir / "config.yml").open("w", encoding="utf-8") as file:
        yaml.dump(config, file)

    subprocess.check_call(["esmvaltool", "run", f"--config-dir={config_dir}", f"{recipe_path}"])  # noqa: S603, S607
    result = next(results_dir.glob("*"))
    return result
