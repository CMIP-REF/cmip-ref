import pathlib

import ilamb3
import pytest
from cmip_ref_metrics_ilamb.example import GlobalMeanTimeseries, calculate_global_mean_timeseries
from cmip_ref_metrics_ilamb.standard import ILAMBStandard, _set_ilamb3_options

from cmip_ref_core.datasets import DatasetCollection, MetricDataset, SourceDatasetType
from cmip_ref_core.metrics import MetricExecutionDefinition


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


def test_annual_mean(metric_dataset):
    annual_mean = calculate_global_mean_timeseries(metric_dataset["cmip6"].path.to_list())
    assert annual_mean.time.size == 132


def test_example_metric(tmp_path, cmip6_data_catalog, mocker):
    metric = GlobalMeanTimeseries()
    ds = cmip6_data_catalog.groupby("instance_id").first()
    output_directory = tmp_path / "output"

    mock_calc = mocker.patch("cmip_ref_metrics_ilamb.example.calculate_global_mean_timeseries")
    mock_calc.return_value.attrs.__getitem__.return_value = "ABC"

    definition = MetricExecutionDefinition(
        output_directory=output_directory,
        output_fragment=pathlib.Path(metric.slug),
        key="global_mean_timeseries",
        metric_dataset=MetricDataset(
            {
                SourceDatasetType.CMIP6: DatasetCollection(ds, "instance_id"),
            }
        ),
    )

    result = metric.run(definition)

    assert mock_calc.call_count == 1

    assert str(result.bundle_filename) == "output.json"

    output_bundle_path = definition.output_directory / definition.output_fragment / result.bundle_filename

    assert result.successful
    assert output_bundle_path.exists()
    assert output_bundle_path.is_file()


def test_standard_site(tmp_path, cmip6_data_catalog):
    metric = ILAMBStandard(registry_file="test.txt", sources={"tas": "test/Site/tas.nc"})
    ds = (
        cmip6_data_catalog[
            (cmip6_data_catalog["experiment_id"] == "historical")
            & (cmip6_data_catalog["variable_id"] == "tas")
        ]
        .groupby("instance_id")
        .first()
    )
    output_directory = tmp_path / "output"
    (output_directory / metric.slug).mkdir(parents=True, exist_ok=True)

    definition = MetricExecutionDefinition(
        output_directory=output_directory,
        output_fragment=pathlib.Path(metric.slug),
        key="ilamb-standard-test_test",
        metric_dataset=MetricDataset(
            {
                SourceDatasetType.CMIP6: DatasetCollection(ds, "instance_id"),
            }
        ),
    )

    result = metric.run(definition)

    assert str(result.bundle_filename) == "output.json"

    output_bundle_path = definition.output_directory / definition.output_fragment / result.bundle_filename

    assert result.successful
    assert output_bundle_path.exists()
    assert output_bundle_path.is_file()


def test_standard_grid(tmp_path, cmip6_data_catalog):
    metric = ILAMBStandard(
        registry_file="test.txt", sources={"gpp": "test/Grid/gpp.nc"}, relationships={"pr": "test/Grid/pr.nc"}
    )
    grp = cmip6_data_catalog[
        (cmip6_data_catalog["experiment_id"] == "historical")
        & ((cmip6_data_catalog["variable_id"] == "gpp") | (cmip6_data_catalog["variable_id"] == "pr"))
    ].groupby(["source_id", "member_id", "grid_label"])
    _, ds = next(iter(grp))
    output_directory = tmp_path / "output"
    (output_directory / metric.slug).mkdir(parents=True, exist_ok=True)

    definition = MetricExecutionDefinition(
        output_directory=output_directory,
        output_fragment=pathlib.Path(metric.slug),
        key="ilamb-standard-test_test",
        metric_dataset=MetricDataset(
            {
                SourceDatasetType.CMIP6: DatasetCollection(ds, "instance_id"),
            }
        ),
    )

    result = metric.run(definition)

    assert str(result.bundle_filename) == "output.json"

    output_bundle_path = definition.output_directory / definition.output_fragment / result.bundle_filename

    assert result.successful
    assert output_bundle_path.exists()
    assert output_bundle_path.is_file()


def test_standard_fail():
    try:
        ILAMBStandard(registry_file="test.txt", sources={"gpp": "test/Grid/gpp.nc", "pr": "test/Grid/pr.nc"})
        assert False
    except ValueError:
        pass


def test_options():
    _set_ilamb3_options("ilamb.txt")
    assert set(["global", "tropical", "arid", "temperate", "cold"]).issubset(ilamb3.conf["regions"])
