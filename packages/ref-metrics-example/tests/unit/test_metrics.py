import pathlib
from unittest import mock

import pytest
from ref_core.datasets import DatasetCollection, MetricDataset, SourceDatasetType
from ref_core.metrics import MetricExecutionDefinition
from ref_metrics_example.example import GlobalMeanTimeseries, calculate_annual_mean_timeseries


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


def test_annual_mean(esgf_data_dir, metric_dataset):
    annual_mean = calculate_annual_mean_timeseries(metric_dataset["cmip6"].path.to_list())

    assert annual_mean.time.size == 286


@mock.patch("ref_metrics_example.example.calculate_annual_mean_timeseries")
def test_example_metric(mock_calc, tmp_path, metric_dataset, cmip6_data_catalog):
    metric = GlobalMeanTimeseries()
    ds = cmip6_data_catalog.groupby("instance_id").first()
    output_directory = tmp_path / "output"

    mock_calc.return_value.attrs.__getitem__.return_value = "ABC"

    configuration = MetricExecutionDefinition(
        output_directory=output_directory,
        output_fragment=pathlib.Path(metric.slug),
        key="global_mean_timeseries",
        metric_dataset=MetricDataset(
            {
                SourceDatasetType.CMIP6: DatasetCollection(ds, "instance_id"),
            }
        ),
    )

    result = metric.run(configuration)

    assert mock_calc.call_count == 1

    assert result.output_bundle == pathlib.Path(metric.slug) / "output.json"

    output_bundle_path = output_directory / result.output_bundle

    assert result.successful
    assert output_bundle_path.exists()
    assert output_bundle_path.is_file()
    assert result.output_bundle.name == "output.json"
