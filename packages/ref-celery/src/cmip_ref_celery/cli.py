"""
CLI for the ref-celery package.
"""

import importlib

import typer

from cmip_ref_celery.app import create_celery_app
from cmip_ref_celery.tasks import register_celery_tasks

app = typer.Typer()


@app.command()
def start_worker(
    loglevel: str = typer.Option("info", help="Log level for the worker"),
    package: str = typer.Option(help="Package to import tasks from"),
    extra_args: list[str] = typer.Argument(None, help="Additional arguments for the worker"),
) -> None:
    """
    Start a Celery worker for the given package.

    A celery worker enables the execution of tasks in the background on multiple different nodes.
    This worker will register a celery task for each metric in the provider.
    The worker tasks can be executed by sending a celery task with the name '{package_name}_{metric_name}'.

    The package must define a 'provider' variable that is an instance of 'ref_core.MetricsProvider'.
    """
    # Create a new celery app
    celery_app = create_celery_app("cmip_ref_celery")

    # Attempt to import the package
    try:
        imp = importlib.import_module(package.replace("-", "_"))
    except ModuleNotFoundError:
        typer.echo(f"Package '{package}' not found")
        raise typer.Abort()

    # Get the provider from the package
    try:
        provider = imp.provider
    except AttributeError:
        typer.echo("The package must define a 'provider' attribute")
        raise typer.Abort()

    # Wrap each metrics in the provider with a celery tasks
    register_celery_tasks(celery_app, provider)

    argv = ["worker", f"--loglevel={loglevel}", *(extra_args or [])]
    celery_app.worker_main(argv=argv)


if __name__ == "__main__":  # pragma: no cover
    app()
