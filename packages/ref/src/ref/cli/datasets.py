"""
View and ingest input datasets
"""

import errno
import os
from pathlib import Path
from typing import Annotated

import pandas as pd
import typer
from loguru import logger
from ref_core.datasets import SourceDatasetType
from rich import box
from rich.console import Console
from rich.table import Table

from ref.datasets import get_dataset_adapter
from ref.models import Dataset
from ref.solver import solve_metrics

app = typer.Typer(help=__doc__)
console = Console()


def _pretty_print_df(df: pd.DataFrame) -> None:
    """
    Pretty print a DataFrame

    Parameters
    ----------
    df
        DataFrame to print
    """
    # Initiate a Table instance to be modified
    max_col_count = console.width // 10
    if len(df.columns) > max_col_count:
        logger.warning(f"Too many columns to display ({len(df.columns)}), truncating to {max_col_count}")
        df = df.iloc[:, :max_col_count]

    table = Table(*[str(column) for column in df.columns])

    for index, value_list in enumerate(df.values.tolist()):
        row = [str(x) for x in value_list]
        table.add_row(*row)

    # Update the style of the table
    table.row_styles = ["none", "dim"]
    table.box = box.SIMPLE_HEAD

    console.print(table)


@app.command(name="list")
def list_(
    ctx: typer.Context,
    source_type: Annotated[
        SourceDatasetType, typer.Option(help="Type of source dataset")
    ] = SourceDatasetType.CMIP6.value,  # type: ignore
    column: Annotated[list[str] | None, typer.Option()] = None,
    include_files: bool = typer.Option(False, help="Include files in the output"),
    limit: int = typer.Option(100, help="Limit the number of rows to display"),
) -> None:
    """
    List the datasets that have been ingested

    The data catalog is sorted by the date that the dataset was ingested (first = newest).
    """
    database = ctx.obj.database

    adapter = get_dataset_adapter(source_type.value)
    data_catalog = adapter.load_catalog(database, include_files=include_files, limit=limit)

    if column:
        if not all(col in data_catalog.columns for col in column):
            logger.error(f"Column not found in data catalog: {column}")
            raise typer.Exit(code=1)
        data_catalog = data_catalog[column]

    _pretty_print_df(data_catalog)


@app.command()
def list_columns(
    ctx: typer.Context,
    source_type: Annotated[
        SourceDatasetType, typer.Option(help="Type of source dataset")
    ] = SourceDatasetType.CMIP6.value,  # type: ignore
    include_files: bool = typer.Option(False, help="Include files in the output"),
) -> None:
    """
    Print the current ref configuration

    If a configuration directory is provided,
    the configuration will attempt to load from the specified directory.
    """
    database = ctx.obj.database

    adapter = get_dataset_adapter(source_type.value)
    data_catalog = adapter.load_catalog(database, include_files=include_files)

    for column in sorted(data_catalog.columns.to_list()):
        print(column)


@app.command()
def ingest(
    ctx: typer.Context,
    file_or_directory: Path,
    source_type: SourceDatasetType = typer.Option(help="Type of source dataset"),
    solve: bool = typer.Option(False, help="Run metrics after ingestion"),
    dry_run: bool = typer.Option(False, help="Do not execute any metrics"),
) -> None:
    """
    Ingest a dataset

    This will register a dataset in the database to be used for metrics calculations.
    """
    config = ctx.obj.config
    db = ctx.obj.database

    logger.info(f"ingesting {file_or_directory}")

    adapter = get_dataset_adapter(source_type.value)

    # Create a data catalog from the specified file or directory
    if not file_or_directory.exists():
        logger.error(f"File or directory {file_or_directory} does not exist")
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_or_directory)

    data_catalog = adapter.find_local_datasets(file_or_directory)
    adapter.validate_data_catalog(data_catalog)

    logger.info(
        f"Found {len(data_catalog)} files for {len(data_catalog[adapter.slug_column].unique())} datasets"
    )
    _pretty_print_df(adapter.pretty_subset(data_catalog))

    for instance_id, data_catalog_dataset in data_catalog.groupby(adapter.slug_column):
        logger.info(f"Processing dataset {instance_id}")

        if dry_run:
            dataset = db.session.query(Dataset).filter_by(slug=instance_id, dataset_type=source_type).first()
            if not dataset:
                logger.info(f"Would save dataset {instance_id} to the database")
                continue
        else:
            with db.session.begin():
                adapter.register_dataset(config, db, data_catalog_dataset)

    if solve:
        solve_metrics(
            db=db,
            dry_run=dry_run,
        )
