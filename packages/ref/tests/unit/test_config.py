import logging
import re
import sys
from pathlib import Path

import pytest
from attr import evolve

from cmip_ref.config import Config, PathConfig
from cmip_ref_core.exceptions import InvalidExecutorException
from cmip_ref_core.executor import Executor


class TestConfig:
    def test_load_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("REF_CONFIGURATION", str(tmp_path / "cmip_ref"))

        # The configuration file doesn't exist
        # so it should default to some sane defaults
        assert not (tmp_path / "ref.toml").exists()

        loaded = Config.load(Path("ref.toml"))

        assert loaded.paths.data == tmp_path / "cmip_ref" / "data"

        # The results aren't serialised back to disk
        assert not (tmp_path / "ref.toml").exists()
        assert loaded._raw is None
        assert loaded._config_file == Path("ref.toml")

    def test_default(self, config):
        config.paths.data = "data"
        config.save()

        # The default location is overridden in the config fixture
        loaded = Config.default()
        assert loaded.paths.data == Path("data")

    def test_load(self, config, tmp_path):
        res = config.dump(defaults=True)

        with open(tmp_path / "ref.toml", "w") as fh:
            fh.write(res.as_string())

        loaded = Config.load(tmp_path / "ref.toml")

        assert config.dumps() == loaded.dumps()

    def test_load_extra_keys(self, tmp_path, caplog):
        content = """[paths]
data = "data"
extra_key = "extra"
another_key = "extra"

[db]
filename = "sqlite://cmip_ref.db"
"""

        with open(tmp_path / "ref.toml", "w") as fh:
            fh.write(content)

        with caplog.at_level(logging.WARNING):
            Config.load(tmp_path / "ref.toml")

        assert len(caplog.records) == 2
        # The order for multiple keys isn't stable
        assert "@ $.paths" in caplog.records[0].message
        assert "extra_key" in caplog.records[0].message
        assert "another_key" in caplog.records[0].message
        assert "extra fields found (filename) @ $.db" in caplog.records[1].message

        for record in caplog.records:
            assert record.levelname == "WARNING"

    def test_invalid(self, tmp_path, caplog):
        content = """[paths]
    data = 1

    [db]
    filename = "sqlite://cmip_ref.db"
    """

        with open(tmp_path / "ref.toml", "w") as fh:
            fh.write(content)

        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match=f"Error loading configuration from {tmp_path / 'ref.toml'}"):
                Config.load(tmp_path / "ref.toml")

        assert len(caplog.records) == 2
        assert "extra fields found (filename) @ $.db" in caplog.records[0].message
        assert caplog.records[0].levelname == "WARNING"

        if sys.version_info >= (3, 12):
            expected_msg = (
                "argument should be a str or an os.PathLike object where __fspath__ returns a str, "
                "not 'Integer'"
            )
        else:
            expected_msg = "expected str, bytes or os.PathLike object, not Integer"
        assert f"invalid type ({expected_msg}) @ $.paths.data" in caplog.records[1].message
        assert caplog.records[1].levelname == "ERROR"

    def test_save(self, tmp_path):
        config = Config(paths=PathConfig(data=Path("data")))

        with pytest.raises(ValueError):
            # The configuration file hasn't been set as it was created directly
            config.save()

        config.save(tmp_path / "ref.toml")

        assert (tmp_path / "ref.toml").exists()

    def test_defaults(self, monkeypatch):
        monkeypatch.setenv("REF_CONFIGURATION", "test")

        cfg = Config.load(Path("test.toml"))

        with_defaults = cfg.dump(defaults=True)

        without_defaults = cfg.dump(defaults=False)

        assert without_defaults == {
            "metric_providers": [
                {"provider": "cmip_ref_metrics_esmvaltool.provider"},
                {"provider": "cmip_ref_metrics_ilamb.provider"},
                {"provider": "cmip_ref_metrics_pmp.provider"},
            ],
        }
        assert with_defaults == {
            "metric_providers": [
                {
                    "provider": "cmip_ref_metrics_esmvaltool.provider",
                    "config": {},
                },
                {
                    "provider": "cmip_ref_metrics_ilamb.provider",
                    "config": {},
                },
                {
                    "provider": "cmip_ref_metrics_pmp.provider",
                    "config": {},
                },
            ],
            "executor": {"executor": "cmip_ref.executor.local.LocalExecutor", "config": {}},
            "paths": {
                "data": "test/data",
                "log": "test/log",
                "scratch": "test/scratch",
                "results": "test/results",
                "allow_out_of_tree_datasets": True,
            },
            "db": {"database_url": "sqlite:///test/db/cmip_ref.db", "run_migrations": True},
        }

    def test_from_env_variables(self, monkeypatch, config):
        monkeypatch.setenv("REF_DATABASE_URL", "test-database")
        monkeypatch.setenv("REF_EXECUTOR", "new-executor")
        monkeypatch.setenv("REF_DATA_ROOT", "/my/test/data")
        monkeypatch.setenv("REF_SCRATCH_ROOT", "/my/test/scratch")
        monkeypatch.setenv("REF_LOG_ROOT", "/my/test/logs")
        monkeypatch.setenv("REF_RESULTS_ROOT", "/my/test/results")

        config_new = config.refresh()

        assert config_new.db.database_url == "test-database"
        assert config_new.executor.executor == "new-executor"
        assert config_new.paths.data == Path("/my/test/data")
        assert config_new.paths.scratch == Path("/my/test/scratch")
        assert config_new.paths.log == Path("/my/test/logs")
        assert config_new.paths.results == Path("/my/test/results")

    def test_executor_build(self, config):
        executor = config.executor.build()
        assert executor.name == "local"
        assert isinstance(executor, Executor)

        # None of the executors support initialisation arguments yet so this is a bit of a placeholder
        config.executor.config["test"] = "value"

        match = re.escape("LocalExecutor.__init__() got an unexpected keyword argument 'test'")
        with pytest.raises(TypeError, match=match):
            config.executor.build()

    def test_executor_build_invalid(self, config):
        config.executor = evolve(config.executor, executor="cmip_ref.config.DbConfig")

        match = "Expected an Executor, got <class 'cmip_ref.config.DbConfig'>"
        with pytest.raises(InvalidExecutorException, match=match):
            config.executor.build()
