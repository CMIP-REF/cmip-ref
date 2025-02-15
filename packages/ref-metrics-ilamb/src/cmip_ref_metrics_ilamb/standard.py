from typing import Any

import ilamb3.regions as ilr  # type: ignore
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
from ilamb3.analysis import bias_analysis  # type: ignore
from ilamb3.exceptions import AnalysisFailure  # type: ignore
from ilamb3.run import generate_html_page, plot_analyses, run_analyses  # type: ignore

from cmip_ref_core.datasets import FacetFilter, SourceDatasetType
from cmip_ref_core.metrics import (
    DataRequirement,
    Metric,
    MetricExecutionDefinition,
    MetricResult,
)
from cmip_ref_core.pycmec.metric import CMECMetric
from cmip_ref_core.pycmec.output import CMECOutput
from cmip_ref_metrics_ilamb.datasets import (
    ILAMB_DATA_VERSION,
    ILAMBRegistryFile,
    build_ilamb_data_registry,
    registry_to_collection,
)


def _add_overall_score(df: pd.DataFrame) -> pd.DataFrame:
    add = (
        df[df["type"] == "score"].groupby(["source", "region", "name"]).mean(numeric_only=True).reset_index()
    )
    add["name"] = "Overall Score [1]"
    add["type"] = "score"
    add["units"] = "1"
    df = pd.concat([df, add]).reset_index(drop=True)
    return df


def _build_cmec_bundle(name: str, df: pd.DataFrame) -> dict[str, Any]:
    ilamb_regions = ilr.Regions()
    bundle = {
        "SCHEMA": {"name": "CMEC", "version": "v1", "package": "ILAMB"},
        "DIMENSIONS": {
            "json_structure": ["region", "model", "metric"],
            "region": {
                r: {
                    "LongName": "None" if r == "None" else ilamb_regions.get_name(r),
                    "Description": "Reference data extents" if r == "None" else ilamb_regions.get_name(r),
                    "Generator": "N/A" if r == "None" else ilamb_regions.get_source(r),
                }
                for r in df["region"].unique()
            },
            "model": {m: {"Description": m, "Source": m} for m in df["source"].unique() if m != "Reference"},
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


class ILAMBStandard(Metric):
    """
    Apply the standard ILAMB analysis with respect to a given reference dataset.
    """

    def __init__(
        self,
        variable_id: str,
        collection_key: str,
        registry_file: ILAMBRegistryFile,
    ):
        # Programatically setup the metric
        self.variable_id = variable_id
        self.collection_key = collection_key
        self.name = f"ILAMB Standard {collection_key}"
        self.slug = self.name.lower().replace(" ", "-")
        self.data_requirements = (
            DataRequirement(
                source_type=SourceDatasetType.CMIP6,
                filters=(
                    FacetFilter(facets={"variable_id": self.variable_id}),
                    FacetFilter(facets={"frequency": "mon"}),
                    FacetFilter(facets={"experiment_id": ("historical", "land-hist")}),
                ),
                group_by=("experiment_id",),
            ),
        )

        self.ilamb_data = registry_to_collection(build_ilamb_data_registry(registry_file, ILAMB_DATA_VERSION))

        # Check that the collection key exists and associate it with this class instance
        df = self.ilamb_data.datasets.set_index(self.ilamb_data.slug_column)
        self.reference_data = df.loc[collection_key].to_dict()

    def run(self, definition: MetricExecutionDefinition) -> MetricResult:
        """
        Run the ILAMB standard analysis.
        """
        reference_dataset = xr.open_dataset(self.reference_data["path"])
        analyses = {"Bias": bias_analysis(self.variable_id)}

        # Phase 1: loop over each model in the group and run an analysis function
        dfs = []
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

            # Run the analysis on the data/model pair
            com = xr.open_mfdataset(sorted(grp["path"].to_list()))
            try:
                df_scalars, ds_ref, ds_com[source_name] = run_analyses(reference_dataset, com, analyses)
            except Exception:  # pragma: no cover
                raise AnalysisFailure(self.name, source_name)
            df_scalars["source"] = df_scalars["source"].str.replace("Comparison", source_name)
            dfs += [df_scalars]

            # Write out the artifacts to the output directories
            df_scalars.to_csv(csv_file, index=False)
            if not ref_file.is_file():  # pragma: no cover
                ds_ref.to_netcdf(ref_file)
            ds_com[source_name].to_netcdf(com_file)

        # Check that the reference intermediate data really was generated.
        if ds_ref is None:
            raise ValueError("Reference intermediate data was not generated.")  # pragma: no cover
        ds_ref.attrs = reference_dataset.attrs

        # Phase 2: get plots and combine scalars and save
        df = pd.concat(dfs).drop_duplicates(subset=["source", "region", "analysis", "name"])
        df = _add_overall_score(df)
        try:
            df_plots = plot_analyses(df, ds_ref, ds_com, analyses, definition.output_directory)
        except Exception:  # pragma: no cover
            raise AnalysisFailure(self.name, "plotting")
        for _, row in df_plots.iterrows():
            row["axis"].get_figure().savefig(
                definition.to_output_path(f"{row['source']}_{row['region']}_{row['name']}.png")
            )
        plt.close("all")

        # Generate an output page
        ds_ref.attrs["header"] = f"{self.variable_id} | {self.reference_data['source_id']}"
        html = generate_html_page(df, ds_ref, ds_com, df_plots)
        with open(definition.to_output_path("index.html"), mode="w") as out:
            out.write(html)

        # Write out the bundle
        # the following function actually returns the metric bundle
        metric_bundle = _build_cmec_bundle(definition.key, df)
        CMECMetric.model_validate(metric_bundle)

        # create a empty CMEC output dictionary
        output_bundle = CMECOutput.create_template()
        CMECOutput.model_validate(output_bundle)

        return MetricResult.build_from_output_bundle(
            definition, cmec_output_bundle=output_bundle, cmec_metric_bundle=metric_bundle
        )
