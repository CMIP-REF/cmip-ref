import pytest
from cmip_ref_celery.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


@pytest.fixture
def mock_create_celery_app(mocker):
    return mocker.patch("cmip_ref_celery.cli.create_celery_app")


@pytest.fixture
def mock_register_celery_tasks(mocker):
    return mocker.patch("cmip_ref_celery.cli.register_celery_tasks")


def test_start_worker_success(mocker, mock_create_celery_app, mock_register_celery_tasks):
    mock_celery_app = mock_create_celery_app.return_value
    mock_provider = mocker.Mock()
    mock_provider.slug = "example"

    mock_import_module = mocker.patch(
        "importlib.import_module", return_value=mocker.Mock(provider=mock_provider)
    )

    result = runner.invoke(app, ["start-worker", "--package", "test_package"])

    assert result.exit_code == 0
    mock_import_module.assert_called_once_with("test_package")
    mock_register_celery_tasks.assert_called_once_with(mock_create_celery_app.return_value, mock_provider)
    mock_celery_app.worker_main.assert_called_once_with(
        argv=["worker", "--loglevel=info", "--queues=example"]
    )


def test_start_core_worker_success(mock_create_celery_app, mock_register_celery_tasks):
    mock_celery_app = mock_create_celery_app.return_value

    result = runner.invoke(app, ["start-worker"])

    assert result.exit_code == 0
    mock_celery_app.worker_main.assert_called_once_with(argv=["worker", "--loglevel=info", "--queues=celery"])


def test_start_worker_success_extra_args(mocker, mock_create_celery_app, mock_register_celery_tasks):
    mock_worker_main = mock_create_celery_app.return_value
    mock_provider = mocker.Mock()
    mock_provider.slug = "example"

    mocker.patch("importlib.import_module", return_value=mocker.Mock(provider=mock_provider))

    result = runner.invoke(
        app,
        [
            "start-worker",
            "--loglevel",
            "error",
            "--package",
            "test_package",
            "--",
            "--extra-args",
            "--concurrency=2",
        ],
    )

    assert result.exit_code == 0, result.output
    mock_worker_main.worker_main.assert_called_once_with(
        argv=["worker", "--loglevel=error", "--queues=example", "--extra-args", "--concurrency=2"]
    )


def test_start_worker_package_not_found(mocker, mock_create_celery_app):
    mock_import_module = mocker.patch("importlib.import_module", side_effect=ModuleNotFoundError)

    result = runner.invoke(app, ["start-worker", "--package", "missing_package"])

    assert result.exit_code == 1
    assert "Package 'missing_package' not found" in result.output
    mock_create_celery_app.assert_called_once_with("cmip_ref_celery")
    mock_import_module.assert_called_once_with("missing_package")


def test_start_worker_missing_provider(mocker, mock_create_celery_app):
    mock_module = mocker.Mock()
    del mock_module.provider
    mock_import_module = mocker.patch("importlib.import_module", return_value=mock_module)

    result = runner.invoke(app, ["start-worker", "--package", "test_package"])

    assert result.exit_code == 1, result.output
    assert "The package must define a 'provider' attribute" in result.output
    mock_import_module.assert_called_once_with("test_package")


def test_list_config():
    result = runner.invoke(app, ["list-config"])

    assert result.exit_code == 0, result.output
    assert "broker_url: 'redis://localhost:6379/1'" in result.stdout
