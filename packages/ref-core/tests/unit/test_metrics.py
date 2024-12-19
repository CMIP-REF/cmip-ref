import re

import pandas as pd
import pytest
from attr import evolve
from ref_core.datasets import FacetFilter, SourceDatasetType
from ref_core.metrics import DataRequirement, MetricExecutionDefinition, MetricResult


class TestMetricResult:
    def test_build(self, tmp_path):
        config = MetricExecutionDefinition(
            output_fragment=tmp_path, key="mocked-metric-slug", metric_dataset=None
        )
        # Setting the output directory generally happens as a side effect of the executor
        config = evolve(config, output_directory=tmp_path)

        result = MetricResult.build_from_output_bundle(config, {"data": "value"})

        assert result.successful
        assert result.output_bundle.exists()
        assert result.output_bundle.is_file()
        with open(result.output_bundle) as f:
            assert f.read() == '{"data": "value"}'

        assert result.output_bundle.is_relative_to(tmp_path)


@pytest.fixture
def apply_data_catalog():
    return pd.DataFrame(
        {
            "variable": ["tas", "pr", "rsut", "tas", "tas"],
            "source_id": ["CESM2", "CESM2", "CESM2", "ACCESS", "CAS"],
        }
    )


@pytest.mark.parametrize(
    "facet_filter, expected_data, expected_index",
    [
        (
            {"variable": "tas"},
            {
                "variable": ["tas", "tas", "tas"],
                "source_id": [
                    "CESM2",
                    "ACCESS",
                    "CAS",
                ],
            },
            [0, 3, 4],
        ),
        (
            {"variable": "tas", "source_id": ["CESM2", "ACCESS"]},
            {
                "variable": ["tas", "tas"],
                "source_id": [
                    "CESM2",
                    "ACCESS",
                ],
            },
            [0, 3],
        ),
    ],
)
def test_apply_filters_single(apply_data_catalog, facet_filter, expected_data, expected_index):
    requirement = DataRequirement(
        source_type=SourceDatasetType.CMIP6,
        filters=(FacetFilter(facet_filter),),
        group_by=None,
    )

    filtered = requirement.apply_filters(apply_data_catalog)

    pd.testing.assert_frame_equal(
        filtered,
        pd.DataFrame(
            expected_data,
            index=expected_index,
        ),
    )


def test_apply_filters_multi(apply_data_catalog):
    requirement = DataRequirement(
        source_type=SourceDatasetType.CMIP6,
        filters=(
            FacetFilter({"variable": "tas"}),
            FacetFilter({"source_id": "ACCESS"}, keep=False),
        ),
        group_by=None,
    )

    filtered = requirement.apply_filters(apply_data_catalog)

    pd.testing.assert_frame_equal(
        filtered,
        pd.DataFrame(
            {
                "variable": ["tas", "tas"],
                "source_id": ["CESM2", "CAS"],
            },
            index=[0, 4],
        ),
    )


def test_apply_filters_dont_keep(apply_data_catalog):
    requirement = DataRequirement(
        source_type=SourceDatasetType.CMIP6,
        filters=(FacetFilter({"variable": "tas"}, keep=False),),
        group_by=None,
    )

    filtered = requirement.apply_filters(apply_data_catalog)

    pd.testing.assert_frame_equal(
        filtered,
        pd.DataFrame(
            {
                "variable": ["pr", "rsut"],
                "source_id": [
                    "CESM2",
                    "CESM2",
                ],
            },
            index=[1, 2],
        ),
    )


def test_apply_filters_missing(apply_data_catalog):
    requirement = DataRequirement(
        source_type=SourceDatasetType.CMIP6,
        filters=(FacetFilter({"missing": "tas"}, keep=False),),
        group_by=None,
    )

    with pytest.raises(
        KeyError,
        match=re.escape("Facet 'missing' not in data catalog columns: ['variable', 'source_id']"),
    ):
        requirement.apply_filters(apply_data_catalog)
