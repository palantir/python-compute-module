# Contributing to `foundry-compute-modules`

## Requirements

* python >= 3.9
* [poetry](https://python-poetry.org/docs/)

## Commands

### Install packages + scripts

This command will install all deps specified in `pyproject.toml` and make the scripts specified in `pyproject.toml` available in your python environment.

```sh
poetry install
```

### Run tests
```sh
poetry run test
```

### Run `mypy` checks
```sh
poetry run check_mypy
```

### Run linter checks (black, ruff, isort)
This will run the same checks as those that are run during CI checks - meaning it will raise any issues found, but not fix them.

```sh
poetry run check_format
```

### Run formatter (black, ruff, isort)
This will actually modify source files to fix any issues identified
```sh
poetry run format
```

### Build the library locally
This will produce a `tar.gz` and a `whl` file in the `./dist` directory. 

```sh
poetry build
```

Either of these files can be installed locally for testing. For example:

```sh
% poetry build
Building foundry-compute-modules (0.0.0)
  - Building sdist
  - Built foundry_compute_modules-0.0.0.tar.gz
  - Building wheel
  - Built foundry_compute_modules-0.0.0-py3-none-any.whl

% pip install ./dist/foundry_compute_modules-0.0.0.tar.gz
```