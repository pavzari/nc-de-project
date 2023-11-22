# Check if .env file exists and include/export variables if present
ifeq ($(wildcard .env),)
$(warning Warning: .env file not found. Some variables might not be set.)
else
include .env
export
endif

PROJECT_NAME = nc-de-project
PYTHON_INTERPRETER = python
WD=$(shell pwd)
PYTHONPATH=${WD}
SHELL := /bin/bash
PROFILE = default
PIP:=pip

## Create python interpreter environment.
create-environment:
	@echo ">>> About to create environment: $(PROJECT_NAME)..."
	@echo ">>> check python3 version"
	( \
		$(PYTHON_INTERPRETER) --version; \
	)
	@echo ">>> Setting up VirtualEnv."
	( \
	    $(PIP) install -q virtualenv virtualenvwrapper; \
	    virtualenv venv --python=$(PYTHON_INTERPRETER); \
	)

# Define utility variable to help calling Python from the virtual environment
ACTIVATE_ENV := source venv/bin/activate

# Execute python related functionalities from within the project's environment
define execute_in_env
	$(ACTIVATE_ENV) && $1
endef

## Build the environment requirements
requirements: create-environment
	$(call execute_in_env, $(PIP) install -r ./requirements.txt)

## Add new environment requirements
add-requirements: 
	$(call execute_in_env, $(PIP) freeze > ./requirements.txt)

## Run the security test (bandit + safety)
security-test:
	$(call execute_in_env, safety check -r ./requirements.txt)
	$(call execute_in_env, bandit -lll */*.py *c/*/*.py)

## Run the flake8 code check
run-flake:
	$(call execute_in_env, flake8  ./src/*/*.py ./test/*.py)

## Run the unit tests
unit-test:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} pytest -v)

## Run the coverage check
check-coverage:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} coverage run --omit 'venv/*' -m pytest && coverage report -m)

## Run all checks
run-checks: security-test run-flake unit-test check-coverage

## Empty ingestion/transformed data s3 buckets
define empty_bucket
	@echo "Emptying S3 bucket: $1"
	@aws s3 rm s3://$1 --recursive
	@echo "S3 bucket $1 has been emptied."
endef

empty-ingestion:
	$(call empty_bucket,$(S3_INGESTION_BUCKET))

empty-transformed:
	$(call empty_bucket,$(S3_TRANSFORMED_BUCKET))

## Empty the data warehouse 
empty-warehouse:
	  @PGPASSWORD=${WDB_PASSWORD} psql -h ${WDB_HOST} -p ${WDB_PORT} -d ${WDB_NAME} -U ${WDB_USER} -c "\
	    DELETE FROM fact_sales_order; \
	    DELETE FROM dim_currency; \
	    DELETE FROM dim_date; \
	    DELETE FROM dim_design; \
	    DELETE FROM dim_location; \
	    DELETE FROM dim_payment_type; \
	    DELETE FROM dim_staff; \
	    DELETE FROM dim_transaction; \
	    DELETE FROM dim_counterparty; \
		DELETE FROM fact_payment; \
		DELETE FROM fact_purchase_order;"
	@echo "Data warehouse has been emptied."

## Empty s3 buckets and data warehouse
empty-all: empty-ingestion empty-transformed empty-warehouse

## Create production database credentials secret in AWS secrets manager
create-production-secret:
	@echo "Creating production database secret..."
	@aws secretsmanager create-secret \
		--name production \
		--description "Production database credentials" \
		--secret-string '{"host":"$(PDB_HOST)","port":$(PDB_PORT),"user":"$(PDB_USER)","password":"$(PDB_PASSWORD)","database":"$(PDB_NAME)"}' \

## Create data warehouse credentials secret in AWS secrets manager
create-warehouse-secret:
	@echo "Creating warehouse database secret..."
	@aws secretsmanager create-secret \
		--name warehouse \
		--description "Warehouse database credentials" \
		--secret-string '{"host":"$(WDB_HOST)","port":$(WDB_PORT),"user":"$(WDB_USER)","password":"$(WDB_PASSWORD)","database":"$(WDB_NAME)"}' \