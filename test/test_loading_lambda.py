from src.loading_lambda.loading_lambda import lambda_handler
from unittest.mock import patch
import datetime
from moto import mock_s3
import subprocess
import logging
import pg8000
import time
import boto3
import pytest
import os

logger = logging.getLogger("TestLogger")
logger.setLevel(logging.INFO)


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="module")
def pg_container_fixture():
    """
    Fixture launches a PostgreSQL container using the specified docker compose file
    (test/docker-compose-dw.yaml). Checks the container's readiness by attempting connections,
    and if successful, database inside the container is set up with a schema (test/mock_db/dw-shema.sql).
    After the test, the fixture tears down the container to clean
    up resources.

    If the container isn't ready within a set number of attempts, a TimeoutError is raised.
    """  # noqa: E501
    test_dir = os.path.dirname(os.path.abspath(__file__))
    compose_path = os.path.join(test_dir, "docker-compose-dw.yaml")
    subprocess.run(
        ["docker", "compose", "-f", compose_path, "up", "-d"], check=False
    )  # noqa: E501
    try:
        max_attempts = 5
        for _ in range(max_attempts):
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "postgres-dw",
                    "pg_isready",
                    "-h",
                    "localhost",
                    "-U",
                    "testdb",
                ],
                stdout=subprocess.PIPE,
                check=False,
            )
            if result.returncode == 0:
                break
            time.sleep(2)
        else:
            raise TimeoutError(
                """PostgreSQL container is not responding,
                cancelling fixture setup."""
            )
        yield
    finally:
        subprocess.run(
            ["docker", "compose", "-f", compose_path, "down"], check=False
        )  # noqa: E501


@pytest.fixture
def s3_fixture():
    with mock_s3():
        s3_client = boto3.client("s3")
        bucket_name = "test-transformed-data-bucket"
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )  # noqa: E501
        yield s3_client, bucket_name


# dim_staff
@patch(
    "src.loading_lambda.loading_lambda.get_credentials",
    return_value={
        "user": "testuser",
        "password": "testpass",
        "database": "testdb",
        "host": "localhost",
        "port": 5433,
    },
)
def test_loading_lambda_dim_staff(
    get_credentials, pg_container_fixture, s3_fixture
):  # noqa E501
    s3_client, s3_bucket = s3_fixture

    with open("test/mock_parquet/data-144511.parquet", "rb") as file:
        s3_client.put_object(
            Body=file.read(),
            Bucket=s3_bucket,
            Key="dim_staff/dim_staff.parquet",  # noqa E501
        )

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": s3_bucket},
                    "object": {"key": "dim_staff/dim_staff.parquet"},
                }
            }
        ]
    }
    lambda_handler(event, "context")

    conn = pg8000.connect(
        user="testuser",
        password="testpass",
        host="localhost",
        port=5433,
        database="testdb",
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * from dim_staff limit 1;")
    result = cursor.fetchone()  # [0]
    assert result == (
        [
            1,
            "Jeremie",
            "Franey",
            "Purchasing",
            "Manchester",
            "jeremie.franey@terrifictotes.com",
        ]
    )


# dim_date
@patch(
    "src.loading_lambda.loading_lambda.get_credentials",
    return_value={
        "user": "testuser",
        "password": "testpass",
        "database": "testdb",
        "host": "localhost",
        "port": 5433,
    },
)
def test_loading_lambda_dim_date(
    get_credentials, pg_container_fixture, s3_fixture
):  # noqa E501
    s3_client, s3_bucket = s3_fixture

    with open("test/mock_parquet/dim_date.parquet", "rb") as file:
        s3_client.put_object(
            Body=file.read(),
            Bucket=s3_bucket,
            Key="dim_date/dim_date.parquet",  # noqa E501
        )

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": s3_bucket},
                    "object": {"key": "dim_date/dim_date.parquet"},
                }
            }
        ]
    }
    lambda_handler(event, "context")

    conn = pg8000.connect(
        user="testuser",
        password="testpass",
        host="localhost",
        port=5433,
        database="testdb",
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * from dim_date limit 1;")
    result = cursor.fetchone()  # [0]
    print(result)
    assert result == [
        datetime.date(2023, 11, 18),
        2023,
        11,
        18,
        6,
        "Saturday",
        "November",
        4,
    ]


# primary key constraint error when inserting into fact_sales_order
@patch(
    "src.loading_lambda.loading_lambda.get_credentials",
    return_value={
        "user": "testuser",
        "password": "testpass",
        "database": "testdb",
        "host": "localhost",
        "port": 5433,
    },
)
def test_loading_lambda_fact_sales_order(
    get_credentials, pg_container_fixture, s3_fixture, caplog
):  # noqa E501
    s3_client, s3_bucket = s3_fixture

    with open("test/mock_parquet/fact_sales_order.parquet", "rb") as file:
        s3_client.put_object(
            Body=file.read(),
            Bucket=s3_bucket,
            Key="fact_sales_order/fact_sales_order.parquet",  # noqa E501
        )

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": s3_bucket},
                    "object": {
                        "key": "fact_sales_order/fact_sales_order.parquet"
                    },  # noqa E501
                }
            }
        ]
    }
    with caplog.at_level(logging.ERROR):
        lambda_handler(event, "context")
        assert (
            "pg8000 - an error has occurred: insert or update on table"
            in caplog.text  # noqa E501
        )


# wrong credentials
@patch(
    "src.loading_lambda.loading_lambda.get_credentials",
    return_value={
        "user": "WRONG",
        "password": "testpass",
        "database": "testdb",
        "host": "localhost",
        "port": 5433,
    },
)
def test_loading_lambda_wrong_cred(
    get_credentials, pg_container_fixture, s3_fixture, caplog
):  # noqa E501
    s3_client, s3_bucket = s3_fixture

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": s3_bucket},
                    "object": {
                        "key": "fact_sales_order/fact_sales_order.parquet"
                    },  # noqa E501
                }
            }
        ]
    }
    with caplog.at_level(logging.ERROR):
        lambda_handler(event, "context")
        assert (
            "pg8000 - an error has occurred: password authentication failed"
            in caplog.text  # noqa E501
        )
