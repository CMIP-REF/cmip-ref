import pytest

from cmip_ref.executor import import_executor_cls
from cmip_ref.executor.local import LocalExecutor
from cmip_ref_core.exceptions import InvalidExecutorException
from cmip_ref_core.executor import Executor


def test_import_executor():
    executor = import_executor_cls("cmip_ref.executor.local.LocalExecutor")

    assert isinstance(executor, Executor)
    assert executor == LocalExecutor


def test_import_executor_missing():
    fqn = "cmip_ref.executor.local.WrongExecutor"
    match = f"Invalid executor: '{fqn}'\n Executor 'WrongExecutor' not found in cmip_ref.executor.local"
    with pytest.raises(InvalidExecutorException, match=match):
        import_executor_cls(fqn)

    fqn = "missing.executor.local.WrongExecutor"
    match = f"Invalid executor: '{fqn}'\n Module 'missing.executor.local' not found"
    with pytest.raises(InvalidExecutorException, match=match):
        import_executor_cls(fqn)


class TestLocalExecutor:
    def test_is_executor(self):
        executor = LocalExecutor()

        assert executor.name == "local"
        assert isinstance(executor, Executor)

    def test_run_metric(self, metric_definition, provider, mock_metric, mocker):
        mock_handle_result = mocker.patch("cmip_ref.executor.local.handle_execution_result")
        mock_execution_result = mocker.MagicMock()
        executor = LocalExecutor()

        executor.run_metric(provider, mock_metric, metric_definition, mock_execution_result)
        # This directory is created by the executor
        assert metric_definition.output_directory.exists()

        mock_handle_result.assert_called_once()
        config, metric_execution_result, result = mock_handle_result.call_args.args

        assert metric_execution_result == mock_execution_result
        assert result.successful
        assert result.bundle_filename == metric_definition.output_directory / "output.json"

    def test_raises_exception(self, mocker, provider, metric_definition, mock_metric):
        mock_handle_result = mocker.patch("cmip_ref.executor.local.handle_execution_result")
        mock_execution_result = mocker.MagicMock()

        executor = LocalExecutor()

        mock_metric.run = lambda definition: 1 / 0

        executor.run_metric(provider, mock_metric, metric_definition, mock_execution_result)

        config, metric_execution_result, result = mock_handle_result.call_args.args
        assert result.successful is False
        assert result.bundle_filename is None

    def test_join(self):
        executor = LocalExecutor()

        executor.join(1)
        # This method should return immediately
