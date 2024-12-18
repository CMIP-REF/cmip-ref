from ref_metrics_esmvaltool import __core_version__, __version__, provider


# Placeholder to get CI working
def test_version():
    assert __version__ == "0.1.0"
    assert __core_version__ == "0.1.0"


def test_provider():
    assert provider.name == "ESMValTool"
    assert provider.slug == "esmvaltool"
    assert provider.version == __version__

    assert len(provider) == 1
