import importlib.resources

from cmip_ref_metrics_ilamb import __version__, provider


def test_provider():
    assert provider.name == "ILAMB"
    assert provider.slug == "ilamb"
    assert provider.version == __version__

    counts = [1]
    for f in importlib.resources.files("cmip_ref_metrics_ilamb.configure").iterdir():
        with open(f) as fin:
            counts.append(fin.read().count("sources"))
    assert len(provider) == sum(counts)
