import pytest
import ref_metrics_esmvaltool
from ref_core.datasets import DatasetCollection, MetricDataset, SourceDatasetType
from ref_core.metrics import MetricExecutionDefinition
from ref_metrics_esmvaltool.example import GlobalMeanTimeseries


@pytest.fixture
def metric_dataset(cmip6_data_catalog) -> MetricDataset:
    selected_dataset = cmip6_data_catalog[
        cmip6_data_catalog["instance_id"] == cmip6_data_catalog.instance_id.iloc[0]
    ]
    return MetricDataset(
        {
            SourceDatasetType.CMIP6: DatasetCollection(
                selected_dataset,
                "instance_id",
            )
        }
    )


def test_example_metric(tmp_path, mocker, metric_dataset, cmip6_data_catalog):
    metric = GlobalMeanTimeseries()
    ds = cmip6_data_catalog.groupby("instance_id", as_index=False).first()

    configuration = MetricExecutionDefinition(
        output_fragment=tmp_path,
        key="global_mean_timeseries",
        metric_dataset=MetricDataset(
            {
                SourceDatasetType.CMIP6: DatasetCollection(ds, "instance_id"),
            }
        ),
    )

    result_dir = configuration.output_fragment / "results" / "recipe_test_a"
    result = result_dir / "work" / "timeseries" / "script1" / "result.nc"

    def mock_check_call(cmd, *args, **kwargs):
        result.parent.mkdir(parents=True)
        result.touch()

    mocker.patch.object(
        ref_metrics_esmvaltool.recipe.subprocess,
        "check_call",
        autospec=True,
        spec_set=True,
        side_effect=mock_check_call,
    )
    open_dataset = mocker.patch.object(
        ref_metrics_esmvaltool.example.xarray,
        "open_dataset",
        autospec=True,
        spec_set=True,
    )
    open_dataset.return_value.attrs.__getitem__.return_value = "ABC"

    result = metric.run(configuration)

    assert result.successful
    assert result.output_bundle.exists()
    assert result.output_bundle.is_file()
    assert result.output_bundle.name == "output.json"
