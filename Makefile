VENV_DIR=venvs/test_venv
PYTHON=python3
SHELL := /bin/bash

all: setup

# ╔═══════════════════════════════╗
# ║ Virtual Environment Functions ║
# ╚═══════════════════════════════╝

$(VENV_DIR):
	@mkdir -p $(VENV_DIR)
	@echo "*" > $(VENV_DIR)/.gitignore
	@echo "Created virtual environment directory $(VENV_DIR)"

create-venv: $(VENV_DIR)
	@$(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created in $(VENV_DIR)"

clean-venv:
	@rm -rf $(VENV_DIR)
	@echo "Removed virtual environment"

venv-upgrade-pip:
	@source $(VENV_DIR)/bin/activate && pip install --upgrade pip

# ╔═══════════════════════════════════════════════╗
# ║ Extra functions for extra packages to install ║
# ╚═══════════════════════════════════════════════╝

install-pack-dev:
	@source $(VENV_DIR)/bin/activate && pip install --editable .

install-req-dev:
	@source $(VENV_DIR)/bin/activate && pip install -e .[dev]
	@echo "Development dependencies installed."

install-req-docs:
	@source $(VENV_DIR)/bin/activate && pip install -e .[docs]
	@echo "Documentation dependencies installed."

install-req-all:
	@source $(VENV_DIR)/bin/activate && pip install -e .[dev,docs]
	@echo "All dependencies installed."

# ╔══════════════════════════════════╗
# ║ All in one create venv and setup ║
# ╚══════════════════════════════════╝

setup-all-dev: create-venv venv-upgrade-pip install-req-all
	@echo "All development setup steps completed."

setup: create-venv venv-upgrade-pip install
	@echo "All setup steps completed."

# Install the package in editable mode for development process
install-dev:
	@source $(VENV_DIR)/bin/activate && pip install --editable .


# Install the package in normal mode for usage
install:
	@source $(VENV_DIR)/bin/activate && pip install .

# ╔══════════════════════════════════════════════════════════╗
# ║ Build source distribution and wheel using pyproject.toml ║
# ╚══════════════════════════════════════════════════════════╝

build:
	@source $(VENV_DIR)/bin/activate && python -m build --sdist --wheel
	@echo "Build completed."

build-check: 
	@source $(VENV_DIR)/bin/activate && python -m twine check dist/*
	@echo "Source distribution with twine check."
	@echo "Build check completed."


build-clean:
	@rm -rf dist/*
	@echo "Cleaned up the dist directory."

# ╔════════════════════╗
# ║ Testing Functions  ║
# ╚════════════════════╝

test:
	@source $(VENV_DIR)/bin/activate && pytest -v --tb=short --disable-warnings --maxfail=1
	@echo "Tests completed."




# ╔═══════════════════╗
# ║ Upload Functions  ║
# ╚═══════════════════╝



upload:
	@echo "To upload, it will need to authenticate the credentials"
	@source $(VENV_DIR)/bin/activate  && twine upload dist/*

upload-test:
	@echo "To upload, it will need to authenticate the credentials"
	@source $(VENV_DIR)/bin/activate  && twine upload -r testpypi --verbose dist/fileagent-$(VERSION)* 
	@echo "Uploaded to Test PyPI."



# ╔═════════════════╗
# ║ Documentations  ║
# ╚═════════════════╝

PDOC_DIR=docs/pdoc/

$(PDOC_DIR):
	@mkdir -p $(PDOC_DIR)
	@echo "Created documentation directory $(PDOC_DIR)"

doc-pdoc: $(PDOC_DIR)
	@echo "Generating documentation using pdoc..."
	@source $(VENV_DIR)/bin/activate && make -C $(PDOC_DIR) create
	@echo "Documentation created."

doc-pdoc-clean: $(PDOC_DIR)
	@echo "Deleting documentation"
	@make -C $(PDOC_DIR) clean
	@echo "Documentation deleted"

doc-pdoc-host:
	@echo "Hosting documentation using pdoc..."
	@source $(VENV_DIR)/bin/activate && make -C $(PDOC_DIR) host


# ╔═════════════════╗
# ║ Extra Functions ║
# ╚═════════════════╝

version-sync:
	@$(PYTHON) scripts/version_tools.py sync-from-pyproject

version-set:
	@$(PYTHON) scripts/version_tools.py set-version




# ╔══════════════╗
# ║ Docker       ║
# ╚══════════════╝

docker-build:
	make -C docker build 

docker-build-alpine:
	make -C docker build-alpine

docker-build-modified:
	make -C docker build-modified


docker-delete:
	make -C docker delete

docker-delete-modified:
	make -C docker delete-modified

docker-delete-alpine:
	make -C docker delete-alpine

docker-push:
	make -C docker push

compose-up:
	make -C docker compose-up

compose-down:
	make -C docker compose-down



# ╔════════════════╗
# ║ Help Function  ║
# ╚════════════════╝

help:
	@echo "Makefile for managing SBOMPY (venv, build, test, docs, docker)."
	@echo ""
	@echo "Targets:"
	@echo "  create-venv           Create a virtual environment."
	@echo "  clean-venv            Remove the virtual environment."
	@echo "  venv-upgrade-pip      Upgrade pip in the virtual environment."
	@echo "  install-pack-dev      Install the package in editable mode (dev)."
	@echo "  install-dev           Install the package in editable mode."
	@echo "  install               Install the package in normal mode."
	@echo "  install-req-dev       Install dev dependencies."
	@echo "  install-req-docs      Install docs dependencies."
	@echo "  install-req-all       Install dev+docs dependencies."
	@echo "  setup-all-dev         Create venv + install all deps."
	@echo "  setup                 Create venv + install package."
	@echo "  build                 Build sdist/wheel."
	@echo "  build-check           Check build with twine."
	@echo "  build-clean           Remove dist artifacts."
	@echo "  test                  Run tests."
	@echo "  upload                Upload to PyPI."
	@echo "  upload-test           Upload to Test PyPI."
	@echo "  doc-pdoc              Generate docs with pdoc."
	@echo "  doc-pdoc-clean        Remove generated docs."
	@echo "  doc-pdoc-host         Host docs with pdoc."
	@echo "  version-sync          Copy version from pyproject.toml to src/sbompy/_version.py."
	@echo "  version-set           Prompt for a version and save it to both version files."
	@echo "  docker-build          Build default Dockerfile."
	@echo "  docker-build-alpine   Build alpine Dockerfile."
	@echo "  docker-build-modified Build modified Dockerfile."
	@echo "  docker-delete         Delete default Docker image."
	@echo "  docker-delete-alpine  Delete alpine Docker image."
	@echo "  docker-delete-modified Delete modified Docker image."
	@echo "  docker-push           Push Docker image."
	@echo "  compose-up            Start docker compose."
	@echo "  compose-down          Stop docker compose."
	@echo ""

.PHONY: all create-venv clean-venv venv-upgrade-pip install-dev install install-req-dev install-req-docs install-req-all setup-all-dev build build-clean test doc-pdoc doc-pdoc-clean doc-pdoc-host version-sync version-set docker-build docker-build-alpine docker-build-local compose-up compose-down help
