# Changelog

Versions follow [Semantic Versioning](https://semver.org/) (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the **Deprecations** section of releases.

<!--
You should *NOT* be adding new changelog entries to this file,
this file is managed by towncrier.
See `changelog/README.md`.

You *may* edit previous changelogs to fix problems like typo corrections or such.
To add a new changelog entry, please see
`changelog/README.md`
and https://pip.pypa.io/en/latest/development/contributing/#news-entries,
noting that we use the `changelog` directory instead of news,
markdown instead of restructured text and use slightly different categories
from the examples given in that link.
-->

<!-- towncrier release notes start -->

## cmip_ref 0.2.0 (2025-03-01)

### Breaking Changes

- Refactor `cmip_ref.env` module to `cmip_ref_core.env` ([#60](https://github.com/CLIMATE-REF/climate-ref/pulls/60))
- Removed `cmip_ref.executor.ExecutorManager` in preference to loading an executor using a fully qualified package name.

  This allows the user to specify a custom executor as configuration
  without needing any change to the REF codebase. ([#77](https://github.com/CLIMATE-REF/climate-ref/pulls/77))
- Renamed the `$.paths.tmp` in the configuration to `$.paths.scratch` to better reflect its purpose.
  This requires a change to the configuration file if you have a custom configuration. ([#89](https://github.com/CLIMATE-REF/climate-ref/pulls/89))
- The REF now uses absolute paths throughout the application.

  This removes the need for a `config.paths.data` directory and the `config.paths.allow_out_of_tree_datasets` configuration option.
  This will enable more flexibility about where input datasets are ingested from.
  Using absolute paths everywhere does add a requirement that datasets are available via the same paths for all nodes/container that may run the REF. ([#100](https://github.com/CLIMATE-REF/climate-ref/pulls/100))
- An [Executor][cmip_ref_core.executor.Executor] now supports only the asynchronous processing of tasks.
  A result is now not returned from the `run_metric` method,
  but instead optionally updated in the database.

  The `run_metric` method also now requires a `provider` argument to be passed in. ([#104](https://github.com/CLIMATE-REF/climate-ref/pulls/104))

### Features

- Adds a `cmip-ref-celery` package to the REF that provides a Celery task queue.

  Celery is a distributed task queue that allows you to run tasks asynchronously.
  This package will be used as a test bed for running the REF in a distributed environment,
  as it can be deployed locally using docker containers. ([#60](https://github.com/CLIMATE-REF/climate-ref/pulls/60))
- Add `metric_providers` and `executor` sections to the configuration which loads the metric provider and executor using a fully qualified package name. ([#77](https://github.com/CLIMATE-REF/climate-ref/pulls/77))
- Implemented Pydantic data models to validate and serialize CMEC metric and output bundles. ([#84](https://github.com/CLIMATE-REF/climate-ref/pulls/84))
- Add the `cmip_ref_celery` CLI commands to the `ref` CLI tool.
  These commands should be available when the `cmip_ref_celery` package is installed.
  The commands should be available in the `ref` CLI tool as `ref celery ...`. ([#86](https://github.com/CLIMATE-REF/climate-ref/pulls/86))
- Add `fetch-sample-data` to the CLI under the `datasets` command.

  ```bash
  ref datasets fetch-sample-data --version v0.3.0 --force-cleanup
  ``` ([#96](https://github.com/CLIMATE-REF/climate-ref/pulls/96))
- Add a [Celery](https://docs.celeryq.dev/en/stable/)-based executor
  to enable asynchronous processing of tasks. ([#104](https://github.com/CLIMATE-REF/climate-ref/pulls/104))
- Add `ref executions list` and `ref executions inspect` CLI commands for interacting with metric executions. ([#108](https://github.com/CLIMATE-REF/climate-ref/pulls/108))

### Improvements

- Move ILAMB/IOMB reference data initialization to a registry-dependent script. ([#83](https://github.com/CLIMATE-REF/climate-ref/pulls/83))
- ILAMB gpp metrics added with full html output and plots. ([#88](https://github.com/CLIMATE-REF/climate-ref/pulls/88))
- Saner error messages for configuration errors ([#89](https://github.com/CLIMATE-REF/climate-ref/pulls/89))
- Centralised the declaration of environment variable overrides of configuration values.

  Renamed the `REF_OUTPUT_ROOT` environment variable to `REF_RESULTS_ROOT` to better reflect its purpose.
  It was previously unused. ([#92](https://github.com/CLIMATE-REF/climate-ref/pulls/92))
- Sample data is now copied to the `test/test-data/sample-data` instead of symlinked.

  This makes it easier to use the sample data with remote executors as the data is now self-contained
  without any links to other parts of the file system. ([#96](https://github.com/CLIMATE-REF/climate-ref/pulls/96))
- Integrated the pycmec validation models into ref core and metric packages ([#99](https://github.com/CLIMATE-REF/climate-ref/pulls/99))
- Added ILAMB relationship analysis to the current metrics and flexibility to define new metrics in ILAMB via a yaml file. ([#101](https://github.com/CLIMATE-REF/climate-ref/pulls/101))
- Sped up the test suite execution ([#103](https://github.com/CLIMATE-REF/climate-ref/pulls/103))

### Improved Documentation

- Added an excerpt from the architecture design document ([#87](https://github.com/CLIMATE-REF/climate-ref/pulls/87))
- Adds a roadmap to the documentation ([#98](https://github.com/CLIMATE-REF/climate-ref/pulls/98))

### Trivial/Internal Changes

- [#97](https://github.com/CLIMATE-REF/climate-ref/pulls/97), [#102](https://github.com/CLIMATE-REF/climate-ref/pulls/102), [#116](https://github.com/CLIMATE-REF/climate-ref/pulls/116), [#118](https://github.com/CLIMATE-REF/climate-ref/pulls/118)


## cmip_ref 0.1.6 (2025-02-03)

### Features

- Added Equilibrium Climate Sensitivity (ECS) to the ESMValTool metrics package. ([#51](https://github.com/CLIMATE-REF/climate-ref/pulls/51))
- Added Transient Climate Response (TCS) to the ESMValTool metrics package. ([#62](https://github.com/CLIMATE-REF/climate-ref/pulls/62))
- Added the possibility to request datasets with complete and overlapping timeranges. ([#64](https://github.com/CLIMATE-REF/climate-ref/pulls/64))
- Added a constraint for selecting supplementary variables, e.g. cell measures or
  ancillary variables. ([#65](https://github.com/CLIMATE-REF/climate-ref/pulls/65))
- Added a sample metric to the ilamb metrics package. ([#66](https://github.com/CLIMATE-REF/climate-ref/pulls/66))
- Added a sample metric to the PMP metrics package. ([#72](https://github.com/CLIMATE-REF/climate-ref/pulls/72))
- - Added the standard ILAMB bias analysis as a metric. ([#74](https://github.com/CLIMATE-REF/climate-ref/pulls/74))

### Bug Fixes

- - Added overlooked code to fully integrate ilamb into ref. ([#73](https://github.com/CLIMATE-REF/climate-ref/pulls/73))
- Correct the expected configuration name to `ref.toml` as per the documentation. ([#82](https://github.com/CLIMATE-REF/climate-ref/pulls/82))

### Improved Documentation

- Update the package name in the changelog.

  This will simplify the release process by fixing the extraction of changelog entries. ([#61](https://github.com/CLIMATE-REF/climate-ref/pulls/61))

### Trivial/Internal Changes

- [#68](https://github.com/CLIMATE-REF/climate-ref/pulls/68)


## cmip_ref 0.1.5 (2025-01-13)

### Trivial/Internal Changes

- [#56](https://github.com/CLIMATE-REF/climate-ref/pulls/56)


## cmip_ref 0.1.4 (2025-01-13)

### Breaking Changes

- Adds an `ingest` CLI command to ingest a new set of data into the database.

  This breaks a previous migration as alembic's `render_as_batch` attribute should have been set
  to support targeting sqlite. ([#14](https://github.com/CLIMATE-REF/climate-ref/pulls/14))
- Renames `ref ingest` to `ref datasets ingest` ([#30](https://github.com/CLIMATE-REF/climate-ref/pulls/30))
- Prepend package names with `cmip_` to avoid conflicting with an existing `PyPI` package.

  This is a breaking change because it changes the package name and all imports.
  All package names will now begin with `cmip_ref`. ([#53](https://github.com/CLIMATE-REF/climate-ref/pulls/53))

### Features

- Migrate to use UV workspaces to support multiple packages in the same repository.
  Adds a `ref-metrics-example` package that will be used to demonstrate the integration of a metric
  package into the REF. ([#2](https://github.com/CLIMATE-REF/climate-ref/pulls/2))
- Adds the placeholder concept of `Executor`'s which are responsible for running metrics
  in different environments. ([#4](https://github.com/CLIMATE-REF/climate-ref/pulls/4))
- Adds the concept of MetricProvider's and Metrics to the core.
  These represent the functionality that metric providers must implement in order to be part of the REF.
  The implementation is still a work in progress and will be expanding in follow-up PRs. ([#5](https://github.com/CLIMATE-REF/climate-ref/pulls/5))
- Add a collection of ESGF data that is required for test suite.

  Package developers should run `make fetch-test-data` to download the required data for the test suite. ([#6](https://github.com/CLIMATE-REF/climate-ref/pulls/6))
- Adds the `ref` package with a basic CLI interface that will allow for users to interact with the database of jobs. ([#8](https://github.com/CLIMATE-REF/climate-ref/pulls/8))
- Add `SqlAlchemy` as an ORM for the database alongside `alembic` for managing database migrations. ([#11](https://github.com/CLIMATE-REF/climate-ref/pulls/11))
- Added a `DataRequirement` class to declare the requirements for a metric.

  This provides the ability to:

  * filter a data catalog
  * group datasets together to be used in a metric calculation
  * declare constraints on the data that is required for a metric calculation

  ([#15](https://github.com/CLIMATE-REF/climate-ref/pulls/15))
- Add a placeholder iterative metric solving scheme ([#16](https://github.com/CLIMATE-REF/climate-ref/pulls/16))
- Extract a data catalog from the database to list the currently ingested datasets ([#24](https://github.com/CLIMATE-REF/climate-ref/pulls/24))
- Translated selected groups of datasets into `MetricDataset`s.
  Each `MetricDataset` contains all of the dataset's needed for a given execution of a metric.

  Added a slug to the `MetricDataset` to uniquely identify the execution
  and make it easier to identify the execution in the logs. ([#29](https://github.com/CLIMATE-REF/climate-ref/pulls/29))
- Adds `ref datasets list` command to list ingested datasets ([#30](https://github.com/CLIMATE-REF/climate-ref/pulls/30))
- Add database structures to represent a metric execution.
  We record previous executions of a metric to minimise the number of times we need to run metrics. ([#31](https://github.com/CLIMATE-REF/climate-ref/pulls/31))
- Added option to skip any datasets that fail validation and to specify the number of cores to
  use when ingesting datasets.
  This behaviour can be opted in using the `--skip-invalid` and `--n-jobs` options respectively. ([#36](https://github.com/CLIMATE-REF/climate-ref/pulls/36))
- Track datasets that were used for different metric executions ([#39](https://github.com/CLIMATE-REF/climate-ref/pulls/39))
- Added an example ESMValTool metric. ([#40](https://github.com/CLIMATE-REF/climate-ref/pulls/40))
- Support the option for different assumptions about the root paths between executors and the ref CLI.

  Where possible path fragments are stored in the database instead of complete paths.
  This allows the ability to move the data folders without needing to update the database. ([#46](https://github.com/CLIMATE-REF/climate-ref/pulls/46))

### Improvements

- Add a bump, release and deploy flow for automating the release procedures ([#20](https://github.com/CLIMATE-REF/climate-ref/pulls/20))
- Migrate test data into standalone [CLIMATE-REF/ref-sample-data](https://github.com/CLIMATE-REF/ref-sample-data) repository.

  The sample data will be downloaded by the test suite automatically into `tests/test-data/sample-data`,
  or manually by running `make fetch-test-data`. ([#49](https://github.com/CLIMATE-REF/climate-ref/pulls/49))

### Bug Fixes

- Adds `version` field to the `instance_id` field for CMIP6 datasets ([#35](https://github.com/CLIMATE-REF/climate-ref/pulls/35))
- Handle missing branch times.
  Fixes [#38](https://github.com/CLIMATE-REF/climate-ref/issues/38). ([#42](https://github.com/CLIMATE-REF/climate-ref/pulls/42))
- Move alembic configuration and migrations to `cmip_ref` package so that they can be included in the distribution. ([#54](https://github.com/CLIMATE-REF/climate-ref/pulls/54))

### Improved Documentation

- Deployed documentation to https://cmip-ref.readthedocs.io/en/latest/ ([#16](https://github.com/CLIMATE-REF/climate-ref/pulls/16))
- General documentation cleanup.

  Added notebook describing the process of executing a notebook locally ([#19](https://github.com/CLIMATE-REF/climate-ref/pulls/19))
- Add Apache licence to the codebase ([#21](https://github.com/CLIMATE-REF/climate-ref/pulls/21))
- Improved developer documentation. ([#47](https://github.com/CLIMATE-REF/climate-ref/pulls/47))

### Trivial/Internal Changes

- [#41](https://github.com/CLIMATE-REF/climate-ref/pulls/41), [#44](https://github.com/CLIMATE-REF/climate-ref/pulls/44), [#48](https://github.com/CLIMATE-REF/climate-ref/pulls/48), [#52](https://github.com/CLIMATE-REF/climate-ref/pulls/52), [#55](https://github.com/CLIMATE-REF/climate-ref/pulls/55)
