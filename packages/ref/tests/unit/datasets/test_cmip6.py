import datetime

import pandas as pd
import pytest

from ref.datasets.cmip6 import CMIP6DatasetAdapter, _parse_datetime


@pytest.fixture
def catalog_regression(data_regression, esgf_data_dir):
    def check(df: pd.DataFrame, basename: str):
        # Strip the path to make the test more robust
        df["path"] = df["path"].str.replace(str(esgf_data_dir), "{esgf_data_dir}")

        data_regression.check(df.to_dict(orient="records"), basename=basename)

    return check


def test_parse_datetime():
    pd.testing.assert_series_equal(
        _parse_datetime(pd.Series(["2021-01-01 00:00:00", "1850-01-17 00:29:59.999993", None])),
        pd.Series(
            [datetime.datetime(2021, 1, 1, 0, 0), datetime.datetime(1850, 1, 17, 0, 29, 59, 999993), None],
            dtype="object",
        ),
    )


class TestCMIP6Adapter:
    def test_catalog_empty(self, db):
        adapter = CMIP6DatasetAdapter()
        df = adapter.load_catalog(db)
        assert df.empty

    def test_load_catalog(self, db_seeded, catalog_regression, esgf_data_dir):
        adapter = CMIP6DatasetAdapter()
        df = adapter.load_catalog(db_seeded)

        for k in adapter.dataset_specific_metadata + adapter.file_specific_metadata:
            assert k in df.columns

        assert len(df) == 9  # unique files
        assert df.groupby("instance_id").ngroups == 5  # unique datasets

        # The order of the rows may be flakey due to sqlite ordering and the created time resolution
        catalog_regression(df.sort_values(["instance_id", "start_time"]), basename="cmip6_catalog_db")

    def test_round_trip(self, db_seeded, esgf_data_dir):
        # Indexes and ordering may be different
        adapter = CMIP6DatasetAdapter()
        local_data_catalog = (
            adapter.find_local_datasets(esgf_data_dir)
            .drop(columns=["time_range"])
            .sort_values(["instance_id", "start_time"])
            .reset_index(drop=True)
        )

        db_data_catalog = (
            adapter.load_catalog(db_seeded).sort_values(["instance_id", "start_time"]).reset_index(drop=True)
        )

        # TODO: start_time has a different dtype from the database due to pandas dt coercion
        db_data_catalog["start_time"] = db_data_catalog["start_time"].astype(object)
        pd.testing.assert_frame_equal(local_data_catalog, db_data_catalog, check_like=True)

    def test_load_local_datasets(self, esgf_data_dir, catalog_regression):
        adapter = CMIP6DatasetAdapter()
        data_catalog = adapter.find_local_datasets(esgf_data_dir)

        # TODO: add time_range to the db?
        assert sorted(data_catalog.columns.tolist()) == sorted(
            [*adapter.dataset_specific_metadata, *adapter.file_specific_metadata, "time_range"]
        )

        catalog_regression(
            data_catalog.sort_values(["instance_id", "start_time"]), basename="cmip6_catalog_local"
        )
