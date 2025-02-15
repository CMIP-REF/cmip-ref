import pytest
from cmip_ref_metrics_pmp.example import AnnualCycle, calculate_annual_cycle

from cmip_ref_core.datasets import DatasetCollection, MetricDataset, SourceDatasetType


@pytest.fixture
def metric_dataset(cmip6_data_catalog) -> MetricDataset:
    selected_dataset = cmip6_data_catalog[
        cmip6_data_catalog["instance_id"]
        == "CMIP6.ScenarioMIP.CSIRO.ACCESS-ESM1-5.ssp126.r1i1p1f1.Amon.tas.gn.v20210318"
    ]
    return MetricDataset(
        {
            SourceDatasetType.CMIP6: DatasetCollection(
                selected_dataset,
                "instance_id",
            )
        }
    )


def test_annual_cycle(sample_data_dir, metric_dataset):
    annual_mean = calculate_annual_cycle(metric_dataset["cmip6"].path.to_list())

    assert annual_mean.time.size == 11


def test_example_metric(metric_dataset, cmip6_data_catalog, mocker, definition_factory):
    metric = AnnualCycle()
    ds = cmip6_data_catalog.groupby("instance_id").first()

    mock_calc = mocker.patch("cmip_ref_metrics_pmp.example.calculate_annual_cycle")

    mock_calc.return_value.attrs.__getitem__.return_value = "ABC"

    definition = definition_factory(cmip6=DatasetCollection(ds, "instance_id"))

    result = metric.run(definition)

    assert mock_calc.call_count == 1

    assert str(result.bundle_filename) == "output.json"

    output_bundle_path = definition.output_directory / result.bundle_filename

    assert result.successful
    assert output_bundle_path.exists()
    assert output_bundle_path.is_file()
