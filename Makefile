SHELL := /usr/bin/env bash
PROJECT_NAME := eibon
PROJECT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))/$(PROJECT_NAME)


.PHONY: unit
unit:
	pytest -v \
		-vv \
		--cov=$(PROJECT_DIR) \
		--capture=no \
		--cov-report=term-missing \
 		--cov-config=.coveragerc \

.PHONY: lint
lint:
	pylint $(PROJECT_DIR)

.PHONY: mypy
mypy:
	mypy $(PROJECT_DIR)

test: lint mypy unit
