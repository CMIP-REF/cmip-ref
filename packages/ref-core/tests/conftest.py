import pytest
from ref_core.datasets import SourceDatasetType
from ref_core.metrics import Configuration, DataRequirement, MetricResult, TriggerInfo
from ref_core.providers import MetricsProvider


class MockMetric:
    name = "mock"

    # This runs on every dataset
    data_requirements = (DataRequirement(source_type=SourceDatasetType.CMIP6, filters=[], group_by=None),)

    def run(self, configuration: Configuration, trigger: TriggerInfo) -> MetricResult:
        return MetricResult(
            output_bundle=configuration.output_directory / "output.json",
            successful=True,
        )


class FailedMetric:
    name = "failed"

    data_requirements = (DataRequirement(source_type=SourceDatasetType.CMIP6, filters=[], group_by=None),)

    def run(self, configuration: Configuration, trigger: TriggerInfo) -> MetricResult:
        return MetricResult(
            successful=False,
        )


@pytest.fixture
def provider() -> MetricsProvider:
    provider = MetricsProvider("mock_provider", "v0.1.0")
    provider.register(MockMetric())
    provider.register(FailedMetric())

    return provider


@pytest.fixture
def mock_metric() -> MockMetric:
    return MockMetric()


@pytest.fixture
def configuration(tmp_path) -> Configuration:
    return Configuration(
        output_directory=tmp_path,
    )
