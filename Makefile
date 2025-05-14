
# ------------------------------------------------------------------------------
# Virtual Environment & Dependencies
# ------------------------------------------------------------------------------
SHELL := /bin/bash
PYTHON_PATH := /opt/homebrew/bin/python3.10
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python

# Clean build artifacts
clean:
	rm -rf dist build *.egg-info $(VENV_DIR)

env: clean
	uv venv $(VENV_DIR) --python=$(PYTHON_PATH)

dev-install: env
	uv pip install --python=$(VENV_PYTHON) -r requirements.txt --no-cache-dir m2c2_datakit


# Register virtualenv with Jupyter as a named kernel
jupyter-kernel:
	$(VENV_PYTHON) -m ipykernel install --user --name="m2c2-datakit-env" --display-name "Python (m2c2-datakit)"

# ------------------------------------------------------------------------------
# Local Development Helpers
# ------------------------------------------------------------------------------

check-deps:
	$(VENV_PYTHON) -c "import scipy, pandas, numpy; print('All core deps are importable ✅')"
