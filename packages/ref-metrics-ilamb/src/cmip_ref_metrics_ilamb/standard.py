from typing import Any

import ilamb3  # type: ignore
import ilamb3.compare as cmp  # type: ignore
import ilamb3.regions as ilr  # type: ignore
import matplotlib.pyplot as plt
import pandas as pd
import pooch
import xarray as xr
from ilamb3 import run
from ilamb3.analysis import add_overall_score  # type: ignore
from loguru import logger

from cmip_ref_core.datasets import FacetFilter, SourceDatasetType
from cmip_ref_core.metrics import (
    DataRequirement,
    Metric,
    MetricExecutionDefinition,
    MetricResult,
)
from cmip_ref_metrics_ilamb.datasets import (
    ILAMB_DATA_VERSION,
    ILAMBRegistryFile,
    build_ilamb_data_registry,
    registry_to_collection,
)


def _build_cmec_bundle(name: str, df: pd.DataFrame) -> dict[str, Any]:
    """
    Build a CMEC boundle from information in the dataframe.

    TODO: Migrate to use pycmec when ready.
    TODO: Add plots and html output.
    """
    ilamb_regions = ilr.Regions()
    bundle = {
        "SCHEMA": {"name": "CMEC", "version": "v1", "package": "ILAMB"},
        "DIMENSIONS": {
            "json_structure": ["region", "model", "metric", "statistic"],
            "dimensions": {
                "region": {
                    r: {
                        "LongName": "None" if r == "None" else ilamb_regions.get_name(r),
                        "Description": "Reference data extents" if r == "None" else ilamb_regions.get_name(r),
                        "Generator": "N/A" if r == "None" else ilamb_regions.get_source(r),
                    }
                    for r in df["region"].unique()
                },
                "model": {
                    m: {"Description": m, "Source": m} for m in df["source"].unique() if m != "Reference"
                },
                "metric": {
                    name: {
                        "Name": name,
                        "Abstract": "benchmark score",
                        "URI": [
                            "https://www.osti.gov/biblio/1330803",
                            "https://doi.org/10.1029/2018MS001354",
                        ],
                        "Contact": "forrest AT climatemodeling.org",
                    }
                },
                "statistic": {
                    "indices": list(df["name"].unique()),
                    "short_names": list(df["name"].unique()),
                },
            },
        },
        "RESULTS": {
            r: {
                m: {
                    name: {
                        s: float(
                            df[(df["source"] == m) & (df["region"] == r) & (df["name"] == s)].iloc[0]["value"]
                        )
                        for s in df["name"].unique()
                    }
                }
                for m in df["source"].unique()
                if m != "Reference"
            }
            for r in df["region"].unique()
        },
    }
    return bundle


def _load_reference_data(
    variable_id: str,
    registry: pooch.Pooch,
    sources: dict[str, str],
    relationships: dict[str, str] | None = None,
) -> xr.Dataset:
    """
    Load the reference data into containers and merge if more than 1 variable is used.
    """
    if relationships is not None:
        sources = sources | relationships
    ref = {key: xr.open_dataset(registry.fetch(str(filename))) for key, filename in sources.items()}
    if len(ref) > 1:
        ref = cmp.trim_time(**ref)
        ref = cmp.same_spatial_grid(ref[variable_id], **ref)
        ds_ref = xr.merge([v for _, v in ref.items()], compat="override")
    else:
        ds_ref = ref[variable_id]
    return ds_ref


def _load_comparison_data(variable_id: str, df: pd.DataFrame) -> xr.Dataset:
    """
    Load the comparison (model) data into containers and merge if more than 1 variable is used.
    """
    com = {
        var: xr.open_mfdataset(sorted((df[df["variable_id"] == var]["path"]).to_list()))
        for var in df["variable_id"].unique()
    }
    if len(com) > 1:
        ds_com = xr.merge([v for _, v in com.items()], compat="override")
    else:
        ds_com = com[variable_id]
    return ds_com


def _set_ilamb3_options(registry_file: ILAMBRegistryFile) -> None:
    """
    Set options for ILAMB based on which registry file is being used.
    """
    reg = build_ilamb_data_registry(registry_file, ILAMB_DATA_VERSION)
    ilamb_regions = ilr.Regions()
    if registry_file == "test.txt":
        ilamb3.conf.set(regions=[None])
    if registry_file == "ilamb.txt":
        ilamb_regions.add_netcdf(reg.fetch("regions/GlobalLand.nc"))
        ilamb_regions.add_netcdf(reg.fetch("regions/Koppen_coarse.nc"))
        ilamb3.conf.set(regions=["global", "tropical", "arid", "temperate", "cold"])


class ILAMBStandard(Metric):
    """
    Apply the standard ILAMB analysis with respect to a given reference dataset.
    """

    def __init__(
        self,
        registry_file: ILAMBRegistryFile,
        sources: dict[str, str],
        **ilamb_kwargs: Any,
    ):
        # Setup the metric
        if len(sources) != 1:
            raise ValueError("Only single source ILAMB metrics have been implemented.")
        self.variable_id = next(iter(sources.keys()))
        self.collection_key = sources[self.variable_id].split("/")[1]
        if "sources" not in ilamb_kwargs:
            ilamb_kwargs["sources"] = sources
        if "relationships" not in ilamb_kwargs:
            ilamb_kwargs["relationships"] = {}
        self.ilamb_kwargs = ilamb_kwargs

        # REF stuff
        self.name = f"{self.variable_id} {self.collection_key}"
        self.slug = self.name.lower().replace(" ", "-")
        self.data_requirements = (
            DataRequirement(
                source_type=SourceDatasetType.CMIP6,
                filters=(
                    FacetFilter(
                        facets={
                            "variable_id": [
                                self.variable_id,
                                *ilamb_kwargs.get("relationships", {}).keys(),
                            ]
                        }
                    ),
                    FacetFilter(facets={"frequency": "mon"}),
                    FacetFilter(facets={"experiment_id": ("historical", "land-hist")}),
                ),
                group_by=("experiment_id",),
            ),
        )

        # Setup ILAMB data and options
        self.registry_file = registry_file
        self.registry = build_ilamb_data_registry(registry_file, ILAMB_DATA_VERSION)
        self.ilamb_data = registry_to_collection(self.registry)

    def run(self, definition: MetricExecutionDefinition) -> MetricResult:
        """
        Run the ILAMB standard analysis.
        """
        plt.rcParams.update({"figure.max_open_warning": 0})
        _set_ilamb3_options(self.registry_file)
        setup = self.ilamb_kwargs
        variable, analyses = run.setup_analyses(self.registry, **setup)

        # Phase I: loop over each model in the group and run an analysis function
        df_all = []
        ds_com = {}
        ds_ref = None
        for _, grp in definition.metric_dataset[SourceDatasetType.CMIP6].datasets.groupby(
            ["source_id", "member_id", "grid_label"]
        ):
            row = grp.iloc[0]

            # Define what we will call the output artifacts
            source_name = "{source_id}-{member_id}-{grid_label}".format(**row.to_dict())
            csv_file = definition.to_output_path(f"{source_name}.csv")
            ref_file = definition.to_output_path("Reference.nc")
            com_file = definition.to_output_path(f"{source_name}.nc")
            log_file = definition.to_output_path(f"{source_name}.log")
            log_id = logger.add(log_file, backtrace=True, diagnose=True)

            try:
                # Load data and run comparison
                ref = _load_reference_data(variable, self.registry, setup["sources"], setup["relationships"])
                com = _load_comparison_data(variable, grp)
                dfs, ds_ref, ds_com[source_name] = run.run_analyses(ref, com, analyses)
                dfs["source"] = dfs["source"].str.replace("Comparison", source_name)

                # Write out artifacts
                dfs.to_csv(csv_file, index=False)
                if not ref_file.is_file():  # pragma: no cover
                    ds_ref.to_netcdf(ref_file)
                ds_com[source_name].to_netcdf(com_file)
                df_all.append(dfs)
            except Exception:
                logger.exception(f"ILAMB analysis {self.slug} failed for {source_name}.")
                continue

            # Pop log and remove zero size files
            logger.remove(log_id)
            if log_file.stat().st_size == 0:
                log_file.unlink()

        # Check that the reference intermediate data really was generated.
        if ds_ref is None:
            raise ValueError("Reference intermediate data was not generated.")  # pragma: no cover
        ds_ref.attrs = ref.attrs

        # Phase 2: get plots and combine scalars and save
        df = pd.concat(df_all).drop_duplicates(subset=["source", "region", "analysis", "name"])
        df = add_overall_score(df)
        df_plots = run.plot_analyses(df, ds_ref, ds_com, analyses, definition.output_directory)
        for _, row in df_plots.iterrows():
            row["axis"].get_figure().savefig(
                definition.to_output_path(f"{row['source']}_{row['region']}_{row['name']}.png")
            )
        plt.close("all")

        # Generate an output page
        ds_ref.attrs["header"] = f"{self.variable_id} | {self.collection_key}"
        html = run.generate_html_page(df, ds_ref, ds_com, df_plots)
        with open(definition.to_output_path("index.html"), mode="w") as out:
            out.write(html)

        # Write out the bundle
        bundle = _build_cmec_bundle(definition.key, df)
        return MetricResult.build_from_output_bundle(definition, bundle)
