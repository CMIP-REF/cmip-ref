from pathlib import Path

from ref.datasets.cmip6 import CMIP6DatasetAdapter
from ref.models import Dataset
from ref.models.dataset import CMIP6Dataset, CMIP6File


def test_ingest_help(invoke_cli):
    result = invoke_cli(["datasets", "ingest", "--help"])

    assert "Ingest a dataset" in result.stdout


class TestDatasetsList:
    def test_list(self, db_seeded, invoke_cli):
        result = invoke_cli(["datasets", "list"])
        assert "experi…" in result.stdout

    def test_list_limit(self, db_seeded, invoke_cli):
        result = invoke_cli(["datasets", "list", "--limit", "1", "--column", "instance_id"])
        assert len(result.stdout.strip().split("\n")) == 3  # header + spacer + 1 row

    def test_list_column(self, db_seeded, invoke_cli):
        result = invoke_cli(["datasets", "list", "--column", "variable_id"])
        assert "variable_id" in result.stdout
        assert "grid" not in result.stdout

    def test_list_column_invalid(self, db_seeded, invoke_cli):
        invoke_cli(["datasets", "list", "--column", "wrong"], expected_exit_code=1)


class TestDatasetsListColumns:
    def test_list(self, db_seeded, invoke_cli):
        result = invoke_cli(["datasets", "list-columns"])
        assert result.stdout.strip() == "\n".join(
            sorted(CMIP6DatasetAdapter().load_catalog(db_seeded, include_files=False).columns.to_list())
        )

    def test_list_include_files(self, db_seeded, invoke_cli):
        result = invoke_cli(["datasets", "list-columns", "--include-files"])
        assert result.stdout.strip() == "\n".join(
            sorted(CMIP6DatasetAdapter().load_catalog(db_seeded, include_files=True).columns.to_list())
        )
        assert "start_time" in result.stdout


class TestIngest:
    data_dir = Path("CMIP6") / "ScenarioMIP" / "CSIRO" / "ACCESS-ESM1-5" / "ssp126" / "r1i1p1f1"

    def test_ingest(self, esgf_data_dir, db, invoke_cli):
        invoke_cli(["datasets", "ingest", str(esgf_data_dir / self.data_dir), "--source-type", "cmip6"])

        assert db.session.query(Dataset).count() == 5
        assert db.session.query(CMIP6Dataset).count() == 5
        assert db.session.query(CMIP6File).count() == 9

    def test_ingest_and_solve(self, esgf_data_dir, db, invoke_cli):
        result = invoke_cli(
            [
                "--log-level",
                "info",
                "datasets",
                "ingest",
                str(esgf_data_dir / self.data_dir),
                "--source-type",
                "cmip6",
                "--solve",
                "--dry-run",
            ],
        )
        assert "Solving for metrics that require recalculation." in result.stderr

    def test_ingest_multiple_times(self, esgf_data_dir, db, invoke_cli):
        invoke_cli(
            [
                "datasets",
                "ingest",
                str(esgf_data_dir / self.data_dir / "Amon" / "tas"),
                "--source-type",
                "cmip6",
            ],
        )

        assert db.session.query(Dataset).count() == 1
        assert db.session.query(CMIP6File).count() == 2

        invoke_cli(
            [
                "datasets",
                "ingest",
                str(esgf_data_dir / self.data_dir / "Amon" / "tas"),
                "--source-type",
                "cmip6",
            ],
        )

        assert db.session.query(Dataset).count() == 1

        invoke_cli(
            [
                "datasets",
                "ingest",
                str(esgf_data_dir / self.data_dir / "Amon" / "rsut"),
                "--source-type",
                "cmip6",
            ],
        )

        assert db.session.query(Dataset).count() == 2

    def test_ingest_missing(self, esgf_data_dir, db, invoke_cli):
        result = invoke_cli(
            [
                "datasets",
                "ingest",
                str(esgf_data_dir / "missing"),
                "--source-type",
                "cmip6",
            ],
            expected_exit_code=1,
        )
        assert isinstance(result.exception, FileNotFoundError)
        assert result.exception.filename == esgf_data_dir / "missing"

        assert f'File or directory {esgf_data_dir / "missing"} does not exist' in result.stderr

    def test_ingest_dryrun(self, esgf_data_dir, db, invoke_cli):
        invoke_cli(
            [
                "datasets",
                "ingest",
                str(esgf_data_dir),
                "--source-type",
                "cmip6",
                "--dry-run",
            ]
        )

        # Check that no data was loaded
        assert db.session.query(Dataset).count() == 0
