## >>> DO NOT EDIT! DO NOT EDIT! DO NOT EDIT! DO NOT EDIT! DO NOT EDIT! DO NOT EDIT! <<<
##
## This file created by otica from otica.yaml and will be
## overwritten the next time it is run.
##
## Put local Makefile targets in common/makefile_parts/something.mk
##
## >>> DO NOT EDIT! DO NOT EDIT! DO NOT EDIT! DO NOT EDIT! DO NOT EDIT! DO NOT EDIT! <<<

THIS_MAKEFILE := $(realpath $(lastword $(MAKEFILE_LIST)))
PATH := ${SCRIPTS_DIR}:${PATH}

# These are subdirectories of the Otica project:
ifndef COMMON
    COMMON := ../common
endif
TEMPLATES := ${COMMON}/templates
ARTIFACTS := ${COMMON}/artifacts

CURRENT_DIR := $(notdir $(patsubst %/,%,$(CURDIR)))

## ENVIRONMENT VARIABLE FILES
include ${COMMON}/env_variables/framework.var
include ${COMMON}/env_variables/gcp-uit-et-iedo-services.var
include ${COMMON}/env_variables/common.var
include local.var

## END OF ENVIRONMENT VARIABLE FILES

# Export all variables:
export

# FRAMEWORK SYNC

# We want to run framework-sync.sh every time make runs this file even
# when no make target is provided. We do this by creating a "fake"
# variable that uses := (no recursive expansion) and the "shell" command.
# However, the variables defined in the above 'includes' are not exported
# in a "shell" command and framework-sync.sh needs those variables. To get
# around this we create a special target called "update-otica-source" (see
# end of this file) and have the "shell" command call "make" on that
# target.

# In order that we don't get into an infinite loop of "make" calling
# itself forever, we use a special indicator variable UPDATE_SOURCE that
# we define when calling "make update-otica-source". We call the "shell"
# script variable definition only when UPDATE_SOURCE is _not_ defined.
# This avoids getting into an infinite loop.

ifeq ($(MAKELEVEL),0)
    ifndef UPDATE_SOURCE
        FAKE_VARIABLE := $(shell >&2 UPDATE_SOURCE="DEFINED" $(MAKE) update-otica-source)
    endif
endif
# END FRAMEWORK SYNC

## OTICA-SUPPLIED MAKEFILES
include ${FRAMEWORK_DIR}/makefile_parts/framework.mk
include ${FRAMEWORK_DIR}/makefile_parts/vault.mk
include ${FRAMEWORK_DIR}/makefile_parts/authenticate.mk
include ${FRAMEWORK_DIR}/makefile_parts/python/pvenv.mk
## END OF OTICA-SUPPLIED MAKEFILES

## TOPLEVEL MAKEFILES
## END OF TOPLEVEL MAKEFILES

## LOCAL MAKEFILES IN COMMON
include ${COMMON}/makefile_parts/app.mk
## END OF LOCAL MAKEFILES

# Get the release channel name from git branches,
# i.e. alpha, beta, and stable
# note: master branch is mapped to 'stable'
ifndef COMMIT_BRANCH
	COMMIT_BRANCH=$(shell git rev-parse --abbrev-ref HEAD)
endif
export RELEASE_CHANNEL=$(shell echo ${COMMIT_BRANCH} | sed 's/master/stable/')

# Update the framework code.
.PHONY: update-otica-source
update-otica-source:
	@${SCRIPTS_DIR}/framework-sync.sh
