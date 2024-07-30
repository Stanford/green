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
