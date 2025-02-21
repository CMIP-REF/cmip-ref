from cmip_ref.models import MetricExecution, MetricExecutionResult


class TestMetricExecution:
    def test_should_run_no_results(self, mocker):
        execution = mocker.Mock(spec=MetricExecution)
        execution.results = []

        assert MetricExecution.should_run(execution, "dataset_hash")

    def test_should_run_invalid_hash(self, mocker):
        execution = mocker.Mock(spec=MetricExecution)
        execution_result = mocker.Mock(spec=MetricExecutionResult)

        execution_result.dataset_hash = "dataset_hash_old"
        execution.results = [execution_result]

        assert MetricExecution.should_run(execution, "dataset_hash")

    def test_should_run_dirty(self, mocker):
        execution = mocker.Mock(spec=MetricExecution)
        execution_result = mocker.Mock(spec=MetricExecutionResult)

        execution_result.dataset_hash = "dataset_hash"
        execution.results = [execution_result]
        execution.dirty = True

        assert MetricExecution.should_run(execution, "dataset_hash")

    def test_shouldnt_run(self, mocker):
        execution = mocker.Mock(spec=MetricExecution)
        execution_result = mocker.Mock(spec=MetricExecutionResult)

        execution_result.dataset_hash = "dataset_hash"
        execution.results = [execution_result]
        execution.dirty = False

        assert not MetricExecution.should_run(execution, "dataset_hash")
