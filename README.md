# CMIP Rapid Evaluation Framework


<!--- --8<-- [start:description] -->

**Status**: This project is in active development. We expect to be ready for beta releases in Q2 2025.

The CMIP Rapid Evaluation Framework is a Python application that provides the ability to rapidly process and
evaluate CMIP data against a set of reference data.
It is designed to be used as a CI/CD pipeline to provide a quick validation of CMIP data.

CMIP REF is a community project, and we welcome contributions from anyone.


[![CI](https://github.com/CLIMATE-REF/climate-ref/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/CLIMATE-REF/climate-ref/actions/workflows/ci.yaml)
[![Coverage](https://codecov.io/gh/CLIMATE-REF/climate-ref/branch/main/graph/badge.svg)](https://codecov.io/gh/CLIMATE-REF/climate-ref)
[![Docs](https://readthedocs.org/projects/climate-ref/badge/?version=latest)](https://cmip-ref.readthedocs.io)

**PyPI :**
[![PyPI](https://img.shields.io/pypi/v/cmip_ref.svg)](https://pypi.org/project/cmip-ref/)
[![PyPI: Supported Python versions](https://img.shields.io/pypi/pyversions/cmip_ref.svg)](https://pypi.org/project/cmip-ref/)

**Other info :**
[![Licence](https://img.shields.io/github/license/CLIMATE-REF/climate-ref.svg)](https://github.com/CLIMATE-REF/climate-ref/blob/main/LICENCE)
[![Last Commit](https://img.shields.io/github/last-commit/CLIMATE-REF/climate-ref.svg)](https://github.com/CLIMATE-REF/climate-ref/commits/main)
[![Contributors](https://img.shields.io/github/contributors/CLIMATE-REF/climate-ref.svg)](https://github.com/CLIMATE-REF/climate-ref/graphs/contributors)

## Getting started

### As a metrics provider

Metrics providers are the core of the REF.
They define the metrics that will be calculated and the data that will be used to calculate them,
by providing a consistent interface for the REF to interact with.

These metrics providers can be run as standalone applications or as part of the REF.

### As a modelling center

The REF is designed to enable Modelling Centers to quickly evaluate their data against a set of reference data.
The data under test here may not be published to ESGF yet,
but the REF can still be used to evaluate it.

```bash
ref datasets ingest {data_path}
ref solve
```

### As a devops engineer

The REF can also be deployed as a standalone set of services that don't require any user interaction.
This is useful for running the REF to automatically evaluate data as it is published to ESGF.

The REF can be run as a set of docker containers, with each service running in its own container.
This allows for easy scaling and deployment of the REF.
These docker containers are not yet published, but can be built from the source code.

```
docker-compose build
```

An example docker-compose file is provided in the repository for the CMIP7 FastTrack deployment of the REF,
using the Celery executor and Redis as the message broker.
This can be run with:

```
docker-compose up
```


<!--- --8<-- [end:description] -->

Full documentation can be found at:
[cmip-ref.readthedocs.io](https://cmip-ref.readthedocs.io/en/latest/).
We recommend reading the docs there because the internal documentation links
don't render correctly on GitHub's viewer.

## Installation

<!--- --8<-- [start:installation] -->

CMIP Rapid Evaluation Framework can be installed with pip, mamba or conda
(mamba and conda releases are not yet implemented):


```bash
pip install cmip_ref
mamba install -c conda-forge cmip_ref
conda install -c conda-forge cmip_ref
```

<!--- --8<-- [end:installation] -->

### For contributors

<!--- sec-begin-installation-dev -->

For information on how to contribute see https://cmip-ref.readthedocs.io/en/latest/development/.

<!--- sec-end-installation-dev -->
