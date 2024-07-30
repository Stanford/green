.PHONY: docs
docs: ## Generate Sphinx docs
	@source ${BUILD_DIR}/venv/bin/activate \
	&& cd ../sphinx-docs/ \
	&& make html

.PHONY: tests
tests: ## Run unit tests
	@source ${BUILD_DIR}/venv/bin/activate \
	&& cd .. \
	&& ./run-tests.sh

.PHONY: mypy
mypy:  ## Run Python static type-checker mypy
	@source ${BUILD_DIR}/venv/bin/activate \
	&& cd .. \
	&& mypy --strict-equality --allow-subclassing-any --allow-any-generics --strict stanford/

