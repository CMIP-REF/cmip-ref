"""
Registry of the currently active providers in the REF

This module provides a registry for the currently active providers.
Often, we can't directly import a provider and it's metrics
as each provider maintains its own virtual environment to avoid dependency conflicts.

For remote providers, a proxy is used to access the metadata associated with the metrics.
These metrics cannot be run locally, but can be executed using other executors.
"""

from attrs import field, frozen
from loguru import logger
from ref_core.providers import MetricsProvider

from ref.database import Database


def _register_provider(db: Database, provider: MetricsProvider) -> None:
    """
    Register a provider with the database

    This is temporary until we have a proper flow for registering providers

    Parameters
    ----------
    provider
        MetricsProvider instance
    """
    from ref.models import Metric, Provider

    provider_model, created = db.get_or_create(
        Provider,
        slug=provider.slug,
        version=provider.version,
        defaults={
            "name": provider.name,
        },
    )
    if created:
        logger.info(f"Created provider {provider.slug}")
        db.session.flush()

    for metric in provider.metrics():
        metric_model, created = db.get_or_create(
            Metric,
            slug=metric.slug,
            provider_id=provider_model.id,
            defaults={
                "name": metric.name,
            },
        )
        if created:
            logger.info(f"Created metric {metric_model.slug}")


@frozen
class ProviderRegistry:
    """
    Registry for the currently active providers

    In some cases we can't directly import a provider and it's metrics,
    in this case we need to proxy the metrics.
    """

    providers: list[MetricsProvider] = field(factory=list)

    @staticmethod
    def build_from_db(db: Database) -> "ProviderRegistry":
        """
        Create a ProviderRegistry instance using information from the database

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
        from ref_metrics_esmvaltool import provider as esmvaltool_provider
        from ref_metrics_example import provider as example_provider

        with db.session.begin_nested():
            _register_provider(db, example_provider)
            _register_provider(db, esmvaltool_provider)
        return ProviderRegistry(providers=[example_provider, esmvaltool_provider])
