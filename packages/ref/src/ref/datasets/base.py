from pathlib import Path
from typing import Protocol

import pandas as pd
from loguru import logger

from ref.config import Config
from ref.database import Database
from ref.models.dataset import Dataset


def _log_duplicate_metadata(
    data_catalog: pd.DataFrame, unique_metadata: pd.DataFrame, slug_column: str
) -> None:
    # Drop out the rows where the values are the same
    invalid_datasets = unique_metadata[unique_metadata.gt(1).any(axis=1)]
    # Drop out the columns where the values are the same
    invalid_datasets = invalid_datasets[invalid_datasets.columns[invalid_datasets.gt(1).any(axis=0)]]

    for instance_id in invalid_datasets.index:
        # Get the columns where the values are different
        invalid_dataset_nunique = invalid_datasets.loc[instance_id]
        invalid_dataset_columns = invalid_dataset_nunique[invalid_dataset_nunique.gt(1)].index.tolist()

        # Include time_range in the list of invalid columns to make debugging easier
        invalid_dataset_columns.append("time_range")

        data_catalog_subset = data_catalog[data_catalog[slug_column] == instance_id]

        logger.error(
            f"Dataset {instance_id} has varying metadata:\n{data_catalog_subset[invalid_dataset_columns]}"
        )


class DatasetAdapter(Protocol):
    """
    An adapter to provide a common interface for different dataset types

    This allows the same code to work with different dataset types.
    """

    dataset_cls: type[Dataset]
    slug_column: str
    dataset_specific_metadata: tuple[str, ...]
    file_specific_metadata: tuple[str, ...] = ()

    def pretty_subset(self, data_catalog: pd.DataFrame) -> pd.DataFrame:
        """
        Get a subset of the data_catalog to pretty print
        """
        ...

    def find_local_datasets(self, file_or_directory: Path) -> pd.DataFrame:
        """
        Generate a data catalog from the specified file or directory

        This data catalog should contain all the metadata needed by the database.
        The index of the data catalog should be the dataset slug.
        """
        ...

    def register_dataset(
        self, config: Config, db: Database, data_catalog_dataset: pd.DataFrame
    ) -> Dataset | None:
        """
        Register a dataset in the database using the data catalog
        """
        ...

    def validate_data_catalog(self, data_catalog: pd.DataFrame, skip_invalid: bool = False) -> pd.DataFrame:
        """
        Validate a data catalog

        Parameters
        ----------
        data_catalog
            Data catalog to validate
        skip_invalid
            If True, ignore datasets with invalid metadata and remove them from the resulting data catalog.

        Raises
        ------
        ValueError
            If `skip_invalid` is False (default) and the data catalog contains validation errors.

        Returns
        -------
        :
            Validated data catalog
        """
        # Check if the data catalog contains the required columns
        missing_columns = set(self.dataset_specific_metadata + self.file_specific_metadata) - set(
            data_catalog.columns
        )
        if missing_columns:
            raise ValueError(f"Data catalog is missing required columns: {missing_columns}")

        # Verify that the dataset specific columns don't vary by dataset by counting the unique values
        # for each dataset and checking if there are any that have more than one unique value.
        unique_metadata = (
            data_catalog[list(self.dataset_specific_metadata)].groupby(self.slug_column).nunique()
        )
        if unique_metadata.gt(1).any(axis=1).any():
            _log_duplicate_metadata(data_catalog, unique_metadata, self.slug_column)

            if skip_invalid:
                data_catalog = data_catalog[
                    ~data_catalog[self.slug_column].isin(
                        unique_metadata[unique_metadata.gt(1).any(axis=1)].index
                    )
                ]
            else:
                raise ValueError("Dataset specific metadata varies by dataset")

        return data_catalog

    def load_catalog(
        self, db: Database, include_files: bool = True, limit: int | None = None
    ) -> pd.DataFrame:
        """
        Load the data catalog from the database

        Returns
        -------
        :
            Data catalog containing the metadata for the currently ingested datasets
        """
        ...
