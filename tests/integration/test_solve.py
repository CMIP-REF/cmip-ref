import ref.solver
from ref.database import Database
from ref.models import Dataset, MetricExecution
from ref.provider_registry import ProviderRegistry, _register_provider


class ExampleProviderRegistry(ProviderRegistry):
    def build_from_db(db: Database) -> "ExampleProviderRegistry":
        """
        Create a ProviderRegistry instance containing only the Example provider.

        Parameters
        ----------
        db
            Database instance

        Returns
        -------
        :
            A new ProviderRegistry instance
        """
        # TODO: We don't yet have any tables to represent metrics providers
        from ref_metrics_example import provider as example_provider

        with db.session.begin_nested():
            _register_provider(db, example_provider)
        return ProviderRegistry(providers=[example_provider])


def test_solve(esgf_data_dir, config, invoke_cli, monkeypatch):
    db = Database.from_config(config)
    monkeypatch.setattr(ref.solver, "ProviderRegistry", ExampleProviderRegistry)
    invoke_cli(["datasets", "ingest", "--source-type", "cmip6", str(esgf_data_dir)])
    assert db.session.query(Dataset).count() == 5

    result = invoke_cli(["--verbose", "solve"])
    assert "Created metric execution ACCESS-ESM1-5_rsut_ssp126_r1i1p1f1" in result.stderr
    assert "Running metric" in result.stderr
    assert db.session.query(MetricExecution).count() == 2

    # Running solve again should not trigger any new metric executions
    result = invoke_cli(["--verbose", "solve"])
    assert "Created metric execution ACCESS-ESM1-5_rsut_ssp126_r1i1p1f1" not in result.stderr
    assert db.session.query(MetricExecution).count() == 2
    execution = db.session.query(MetricExecution).filter_by(key="ACCESS-ESM1-5_rsut_ssp126_r1i1p1f1").one()

    assert len(execution.results[0].datasets) == 1
    assert (
        execution.results[0].datasets[0].instance_id
        == "CMIP6.ScenarioMIP.CSIRO.ACCESS-ESM1-5.ssp126.r1i1p1f1.Amon.rsut.gn.v20210318"
    )
