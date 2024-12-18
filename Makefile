# Makefile to help automate key steps

.DEFAULT_GOAL := help
# Will likely fail on Windows, but Makefiles are in general not Windows
# compatible so we're not too worried
TEMP_FILE := $(shell mktemp)

# A helper script to get short descriptions of each target in the Makefile
define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([\$$\(\)a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-30s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT


.PHONY: help
help:  ## print short description of each target
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.PHONY: pre-commit
pre-commit:  ## run all the linting checks of the codebase
	uv run pre-commit run --all-files


.PHONY: mypy
mypy:  ## run mypy on the codebase
	MYPYPATH=stubs uv run --package ref-core mypy packages/ref-core
	MYPYPATH=stubs uv run --package ref mypy packages/ref
	MYPYPATH=stubs uv run --package ref-metrics-example mypy packages/ref-metrics-example
	MYPYPATH=stubs uv run --package ref-metrics-esmvaltool mypy packages/ref-metrics-esmvaltool

.PHONY: ruff-fixes
ruff-fixes:  ## fix the code using ruff
	uv run ruff check --fix
	uv run ruff format

.PHONY: test-ref
test-ref:  ## run the tests
	uv run --package ref \
		pytest packages/ref \
		-r a -v --doctest-modules --cov=packages/ref/src

.PHONY: test-core
test-core:  ## run the tests
	uv run --package ref-core \
		pytest packages/ref-core \
		-r a -v --doctest-modules --cov=packages/ref-core/src

.PHONY: test-metrics-example
test-metrics-example:  ## run the tests
	uv run --package ref-metrics-example \
		pytest packages/ref-metrics-example \
		-r a -v --doctest-modules --cov=packages/ref-metrics-example/src

.PHONY: test-metrics-esmvaltool
test-metrics-esmvaltool:  ## run the tests
	uv run --package ref-metrics-esmvaltool \
		pytest packages/ref-metrics-esmvaltool \
		-r a -v --doctest-modules --cov=packages/ref-metrics-esmvaltool/src

.PHONY: test-integration
test-integration:  ## run the integration tests
	uv run \
		pytest tests \
		-r a -v

.PHONY: test
test: test-core test-ref test-metrics-example test-metrics-esmvaltool test-integration ## run the tests

# Note on code coverage and testing:
# If you want to debug what is going on with coverage, we have found
# that adding COVERAGE_DEBUG=trace to the front of the below command
# can be very helpful as it shows you if coverage is tracking the coverage
# of all of the expected files or not.

.PHONY: docs
docs:  ## build the docs
	uv run mkdocs build

.PHONY: docs-strict
docs-strict:  ## build the docs strictly (e.g. raise an error on warnings, this most closely mirrors what we do in the CI)
	uv run mkdocs build --strict

.PHONY: docs-serve
docs-serve: ## serve the docs locally
	uv run mkdocs serve

.PHONY: changelog-draft
changelog-draft:  ## compile a draft of the next changelog
	uv run towncrier build --draft

.PHONY: licence-check
licence-check:  ## Check that licences of the dependencies are suitable
	uv export --no-dev > $(TEMP_FILE)
	uv run liccheck -r $(TEMP_FILE) -R licence-check.txt
	rm -f $(TEMP_FILE)

.PHONY: virtual-environment
virtual-environment:  ## update virtual environment, create a new one if it doesn't already exist
	uv sync
	uv run pre-commit install

.PHONY: fetch-test-data
fetch-test-data:  ## Fetch test data
	uv run python ./scripts/fetch_test_data.py
