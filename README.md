This repository contains the code and configuration for a cloud-based ETL data platform for a hypothetical retail client. The solution extracts data from an online transactional processing (OLTP) database at regular intervals and loads the transformed data into an online analytics processing (OLAP) data warehouse.

The target data warehouse is structured following a star schema for optimal query performance and data analysis. Entity-relationship diagrams (ERDs) for the source database and the resulting star schema in the data warehouse are provided below:

- [Source Database ERD](./docs/olap-db.png)
- [Data Warehouse Star Schema ERD](./docs/oltp-db.png)

### Technology Stack

- **AWS Services:** Lambda, S3 for data storage, EventBridge for job scheduling, CloudWatch for logging and monitoring, Secrets Manager for storing database credentials and Quicksight for dashboard creation.
- **Python:** Main ETL Lambda application development.
- **Terraform:** Provisioning and managing AWS resources.
- **Docker:** Database mocking for integration testing.
- **GitHub Actions:** Automated deployment and testing.
- **Makefile:** A Makefile is provided for development tasks such as environment setup, security testing, code checks, and more.

### Pipeline Overview

![pipeline-diagram](./docs/aws-infra-diagram.svg)

- EventBridge triggers the ingestion Lambda function to extract data from the production database at regular intervals [1-2].

- Extracted data is stored in the ingestion S3 bucket as JSON [3].

- The Transformation Lambda, triggered by completed ingestion, remodels the data into a warehouse-friendly format, saving it as Parquet files in the transformed data S3 bucket [4-5].

- The loading Lambda reads Parquet files and updates the data warehouse [6-7].

- CloudWatch provides logging for events and errors, sending email alerts for significant issues during each pipeline step.

### Development Setup

Create a Python virtual environment and install the required packages:

```sh
make requirements
```

Run essential checks: code coverage, bandit + safety for security, flake8 for code style and pytest for unit and integration tests. Docker and docker compose are required for some of the tests. Commands for running individual checks are also provided.

```sh
make run-checks
```

Any additional Python packages installed during development can be added with:

```sh
make add-requirements
```

The .env file at the root of the project is required for some optional commands that can be useful during development. Rename the `.env.example` file to `.env` and update the necessary variables to run the following commands:

Clear the ingestion and transformed data S3 buckets, and empty the data warehouse:

```sh
make empty-ingestion
make empty-transformed
make empty-warehouse
make empty-all
```

Create secrets for the production and warehouse databases in AWS Secrets Manager:

```bash
make create-production-secret
make create-warehouse-secret
```

### Deployment Setup

The Terraform configuration for this project is set up to use an S3 bucket as a backend. Ensure that AWS credentials are configured for the GitHub Actions pipeline to deploy the infrastructure successfully.

Additionally, the extraction and loading Lambdas require appropriate credentials in order to connect to OLTP and OLAP databases. Ensure that these credentials are stored in AWS Secrets Manager.

### Contributors

- Josh Lee
  ([LinkedIn](https://www.linkedin.com/in/josh-lee-6ba53b9b/) |
  [GitHub](https://github.com/J-shLee))

- Zhuangliang Cao
  ([LinkedIn](https://www.linkedin.com/in/zhuangliang-cao-3880b218a/) |
  [GitHub](https://github.com/sd816224))

- Alex Chan
  ([LinkedIn](https://www.linkedin.com/in/alextfchan/) |
  [GitHub](https://github.com/alextfchan))

- Samuel Jukes
  ([LinkedIn](https://www.linkedin.com/in/samuel-jukes-964662277/) |
  [GitHub](https://github.com/Sajuke))

- Ryhan Uddin
  ([LinkedIn](https://www.linkedin.com/in/ryhan-uddin-17b637160/) |
  [GitHub](https://github.com/RyhanU1))

- Pav Z.
  ([LinkedIn]() |
  [GitHub](https://github.com/pavzari))
