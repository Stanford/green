.PHONY: docs
docs: ## Generate Sphinx docs
	@source ${BUILD_DIR}/venv/bin/activate \
	&& cd ../sphinx-docs/ \
	&& make html \
	&& cd .. && sphinx-build ./sphinx-docs/source/ ./sphinx-docs/build/ \
	&& cp -pr sphinx-docs/build/html/* docs/ \
	&& cp -pr docs/* /afs/ir.stanford.edu/users/a/d/adamhl/WWW/webauthed/all-stanford/green/

.PHONY: mypy
mypy:  ## Run Python static type-checker mypy
	@source ${BUILD_DIR}/venv/bin/activate \
	&& cd .. \
	&& mypy --strict-equality --allow-subclassing-any --allow-any-generics --strict stanford/

.PHONY: ruff
ruff:  ## Run the ruff linter
	@source ${BUILD_DIR}/venv/bin/activate \
	&& cd .. \
	&& ruff check stanford/

.PHONY: pylint
pylint:  ## Run Python linter pylint
	@source ${BUILD_DIR}/venv/bin/activate \
	&& cd .. \
	&& pylint stanford/green

#.PHONY: tests
#tests: ## Run unit tests
#	@source ${BUILD_DIR}/venv/bin/activate \
#	&& cd .. \
#	&& ./run-tests.sh

.PHONY: tests
tests: ## Run unit tests
	@source ${BUILD_DIR}/venv/bin/activate \
	&& cd .. \
	&& python run-tests.py --start-dir=${START_DIR}


