import pathlib

import pytest

from cmip_ref.executor import _copy_file_to_results, handle_execution_result, import_executor_cls
from cmip_ref.executor.local import LocalExecutor
from cmip_ref.models import MetricExecutionResult
from cmip_ref_core.exceptions import InvalidExecutorException
from cmip_ref_core.executor import Executor
from cmip_ref_core.metrics import MetricResult


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


@pytest.fixture
def metric_execution_result(mocker):
    mock_result = mocker.Mock(spec=MetricExecutionResult)
    mock_result.output_fragment = "output_fragment"
    return mock_result


def test_handle_execution_result_successful(config, metric_execution_result, mocker, definition_factory):
    result = MetricResult(definition=definition_factory(), successful=True, bundle_filename="bundle.zip")
    mock_copy = mocker.patch("cmip_ref.executor._copy_file_to_results")

    handle_execution_result(config, metric_execution_result, result)

    mock_copy.assert_called_once_with(
        config.paths.scratch, config.paths.results, metric_execution_result.output_fragment, "bundle.zip"
    )
    metric_execution_result.mark_successful.assert_called_once_with("bundle.zip")
    assert not metric_execution_result.metric_execution.dirty


def test_handle_execution_result_failed(config, metric_execution_result, definition_factory):
    result = MetricResult(definition=definition_factory(), successful=False, bundle_filename=None)

    handle_execution_result(config, metric_execution_result, result)

    metric_execution_result.mark_failed.assert_called_once()


def test_copy_file_to_results_success(mocker):
    scratch_directory = pathlib.Path("/scratch")
    results_directory = pathlib.Path("/results")
    fragment = "output_fragment"
    filename = "bundle.zip"

    mocker.patch("pathlib.Path.exists", return_value=True)
    mock_copy = mocker.patch("shutil.copy")

    _copy_file_to_results(scratch_directory, results_directory, fragment, filename)

    mock_copy.assert_called_once_with(
        scratch_directory / fragment / filename, results_directory / fragment / filename
    )


def test_copy_file_to_results_file_not_found(mocker):
    scratch_directory = pathlib.Path("/scratch")
    results_directory = pathlib.Path("/results")
    fragment = "output_fragment"
    filename = "bundle.zip"

    mocker.patch("pathlib.Path.exists", return_value=False)

    with pytest.raises(
        FileNotFoundError, match=f"Could not find {filename} in {scratch_directory / fragment}"
    ):
        _copy_file_to_results(scratch_directory, results_directory, fragment, filename)
