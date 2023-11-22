PROJECT_NAME = nc-de-project
REGION = eu-west-2
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
S3_INGESTION_BUCKET = nc-de-project-ingested-data-bucket-20231102173127149000000003
S3_TRANSFORMED_BUCKET = nc-de-project-transformed-data-20231102173127140100000001
AWS_PROFILE = nc-admin

define empty_bucket
	@echo "Emptying S3 bucket: $1"
	@aws s3 rm s3://$1 --recursive --profile $(AWS_PROFILE)
	@echo "S3 bucket $1 has been emptied."
endef

empty_ingestion_bucket:
	$(call empty_bucket,$(S3_INGESTION_BUCKET))

empty_transformed_bucket:
	$(call empty_bucket,$(S3_TRANSFORMED_BUCKET))

empty-ingestion: empty_ingestion_bucket

empty-transformed: empty_transformed_bucket

## Empty the data warehouse 
DB_HOST = nc-data-eng-project-dw-prod.chpsczt8h1nu.eu-west-2.rds.amazonaws.com
DB_PORT = 5432
DB_NAME = postgres
DB_USER = project_team_5

empty_data_warehouse:
	  @psql -h ${DB_HOST} -p ${DB_PORT} -d ${DB_NAME} -U ${DB_USER} -W -c "\
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

empty-warehouse: empty_data_warehouse

