## Development dependencies

1. [make](https://www.gnu.org/software/make/) - commands control tool
2. [poetry](https://python-poetry.org/) - requirements manager and virtualenv management tool
3. [python 3.8+](https://www.python.org/) - python pre-installed on your machine
4. [pre-commit](https://pre-commit.com/) - (optional) development dependency for checking code quality before commit
## Getting started


### Install pre-commit hooks

```
make pre-commit
```

### Create virtualenv and install dependencies

```
make deps
```

### Run app locally

```
make run
```


### Install app globally in the system and run

```
make install
cli-command --version
cli-command
```

### Code checks (static code analysis)

```
make lint
make cov
```

### Restart project from scratch

```
make clean
```
