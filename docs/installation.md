# Installation

There are several ways to install and use the `cmip_ref` package and associated CLI tool:

## PyPI

You can install `cmip_ref` using `pip`:

```bash
pip install cmip_ref
```

The PyPi package contains some additional extras that bundle some additional dependencies.
Depending on your use case you may want to install additional extras:

* `celery` - for running the REF in a distributed manner
* `providers` - metrics providers for CMIP7-FastTrack

These can be installed using:

```bash
pip install cmip_ref[celery,providers]
```

/// admonition | Note

`pip install cmip_ref[providers]` installs the metric providers packages which container the metrics definitions,
but not necesarily the additional packages required to run the metrics.
///


## Conda

/// admonition | conda-forge
    type: warning

The conda-forge packages are a work in progress and are not yet available.
See [#80](https://github.com/CLIMATE-REF/climate-ref/issues/80) for more information.
///

You can install `cmip_ref` using `mamba` or `conda`:

```bash
mamba install -c conda-forge cmip_ref
conda install -c conda-forge cmip_ref
```

A modern alternative to using `conda` as package a manager is [Pixi](https://pixi.sh/dev/).
Pixi uses the same packages as `conda` but is faster and can create reproducible environments out of the box.


## Docker

You can run `cmip_ref` using Docker. First, build the Docker container from the source code:

```bash
git clone https://github.com/CLIMATE-REF/climate-ref.git
cd climate-ref
docker-compose build
```

Then, run the container:

```bash
docker-compose up
```

## From Source

To install `cmip_ref` from the source code, clone the repository and install it:

```bash
git clone https://github.com/CLIMATE-REF/climate-ref.git
cd climate-ref
make virtual-environment
```

See the [development documentation](development.md) for more information on how to contribute to the project.
