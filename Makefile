.PHONY: test
# target: test - Run tests
test:
	@pytest -v -s []

.PHONY: tox
# target: tox - Run tox for environment testing
tox:
	@tox

.PHONY: pep8
# target: pep8 - Check code against PEP8 standards
pep8:
	@pre-commit run --files smsaero/__init__.py
	@bandit -r smsaero/__init__.py

.PHONY: scenario
# target: scenario - Run custom scenario script
scenario:
	@bash -c "set -o allexport; source .env set; +o allexport; python tests/scenario.py"

.PHONY: coverage
# target: coverage - Calculate code coverage
coverage:
	@coverage run --omit=smsaero/command_line.py -m pytest && coverage report -m

.PHONY: docker-build-and-push
# target: docker-build-and-push - Build and push Docker image
docker-build-and-push:
	@docker buildx create --name smsaero_python --use || docker buildx use smsaero_python
	@docker buildx build --platform linux/amd64,linux/arm64 -t 'smsaero/smsaero_python:latest' . -f Dockerfile --push

.PHONY: docker-shell
# target: docker-shell - Run a shell inside the Docker container
docker-shell:
	@docker run -it --rm 'smsaero/smsaero_python:latest' /bin/bash

.PHONY: clean-build
# target: clean-build - Remove build artifacts
clean-build:
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info

.PHONY: clean-pyc
# target: clean-pyc - Remove Python file artifacts
clean-pyc:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +
	@find . -name '*.log' -exec rm -f {} +

.PHONY: release
# target: release - Release app into PyPi
release: clean-build clean-pyc
	@python -m build --sdist
	@python -m build --wheel
	@echo "Build complete."
	@twine check dist/*
	@echo "Check complete."
	@twine upload dist/*
	@echo "Uploaded successfully."

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile | sed -e 's/^# target: //g'
