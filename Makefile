CODE_DIRS=stock_market_analysis
TEST_DIRS=tests
POETRY_COMMAND=stock-market-analysis

help:  ## these help instructions
	@sed -rn 's/^([a-zA-Z_-]+):.*?## (.*)$$/"\1" "\2"/p' < $(MAKEFILE_LIST)|xargs printf "make %-20s# %s\n"

pre-commit: ## install pre-commit hooks defined in .pre-commit-config.yaml
	pre-commit install

deps: ## install project dependencies
	pre-commit install || echo "Optionally install pre-commit tool using 'pip install pre-commit'"
	poetry --version || (echo "Install poetry using: 'pip install poetry setuptools wheel'" && false)
	poetry config virtualenvs.in-project true
	poetry install
	touch $@

format: deps ## format code according to PEP-8 style
	poetry run ruff --fix $(CODE_DIRS) $(TEST_DIRS)

lint: deps ## check wehther code is formatted according to PEP-8 style
	poetry run ruff check $(CODE_DIRS) $(TEST_DIRS)

type-check: ## check whether python annotations are properly assigned
	poetry run mypy ${CODE_DIRS} ${TEST_DIRS}

unit-tests: deps ## run unit tests
	poetry run pytest -s -vv --doctest-modules $(TEST_FILE)

cov: deps ## run unit tests and should code coverage
	poetry run pytest -s -vv --doctest-modules --cov=$(CODE_DIRS) $(TEST_FILE)

cov-html: deps ## run unit tests and generate HTML report showing code coverage
	poetry run coverage html

checks: lint cov type-check ## run all code checks

install: deps  ## install stock-market-analysis globally in your system
	pip3 install .

build: deps ## build python distribution and wheels
	poetry build

publish: deps build ## publish lib to the (PYPI_USERNAME and PYPI_PASSWORD env vars MUST be exported before publishing)
	@poetry publish --repository pypirepo --username $(PYPI_USERNAME) --password $(PYPI_PASSWORD)

docs: deps ## generate mkdocs-based documentation and save to site/index.html
	poetry run mkdocs build
	echo "Open the docs using ex. 'firefox site/index.html'"

docs-run: deps ## run mkdocs-based doc in the local server
	poetry run mkdocs serve

clean: ## clean virtualenv deps etc.
	rm -rf .venv .pytest_cache .mypy_cache .coverage deps site htmlcov .ruff_cache
	find . -type f -name "*.pyc" | xargs rm -fr
	find . -type d -name __pycache__ | xargs rm -fr


deploy:
	@echo "Deploying the serverless application..."
	serverless deploy

run:
	aws stepfunctions start-execution --state-machine-arn arn:aws:states:eu-west-1:398024481618:stateMachine:StockMarketAnalysisStateMachine

.PHONY: docs deploy run

