from src.ingestion_lambda.ingestion_lambda import lambda_handler
from unittest.mock import patch
from datetime import datetime as dt

# import datetime
from moto import mock_s3
import subprocess
import logging
import time_machine
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


@pytest.fixture(scope="function")
def pg_container_fixture():
    """
    Fixture launches a PostgreSQL container using the specified docker compose file
    (test/docker-compose-prod-db.yaml). Checks the container's readiness by attempting connections,
    and if successful, database inside the container is set up with a schema (test/mock_db/prod-schema.sql)
    and a pg8000 connection object to the database is returned.After the test,
    the fixture tears down the container to clean up resources.

    If the container isn't ready within a set number of attempts, a TimeoutError is raised.
    """  # noqa: E501
    test_dir = os.path.dirname(os.path.abspath(__file__))
    compose_path = os.path.join(test_dir, "docker-compose-prod-db.yaml")
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
                    "postgres-prod",
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
        conn = pg8000.connect(
            user="testuser",
            password="testpass",
            host="localhost",
            port=5433,
            database="testdb",
        )
        yield conn
    finally:
        subprocess.run(
            ["docker", "compose", "-f", compose_path, "down"], check=False
        )  # noqa: E501


@pytest.fixture
def s3_fixture():
    with mock_s3():
        s3_client = boto3.client("s3")
        bucket_name = "test-ingestion-data-bucket"
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )  # noqa: E501
        yield s3_client, bucket_name


@patch(
    "src.ingestion_lambda.ingestion_lambda.get_credentials",
    return_value={
        "user": "testuser",
        "password": "testpass",
        "database": "testdb",
        "host": "localhost",
        "port": 5433,
    },
)
def test_ingestion_lambda_info_logged_if_no_updates(
    get_credentials, pg_container_fixture, s3_fixture, caplog
):  # noqa E501
    """Empty JSON is returned if there are no new updates to the
    production database. Info message is logged informing of the above."""
    s3_client, s3_bucket = s3_fixture

    # put last_update.txt run into a mock s3:
    s3_client.put_object(
        Body="2020:01:01:00:00:00",
        Bucket=s3_bucket,
        Key="last_update.txt",
    )

    # eventbridge scheduler invocation
    event = {"data_bucket_name": s3_bucket}

    with caplog.at_level(logging.INFO):
        lambda_handler(event, "context")
        assert "No new updates to write to file" in caplog.text  # noqa E501


@patch(
    "src.ingestion_lambda.ingestion_lambda.get_credentials",
    return_value={
        "user": "testuser",
        "password": "testpass",
        "database": "testdb",
        "host": "localhost",
        "port": 5433,
    },
)
@time_machine.travel(dt(2023, 1, 1, 17, 30, 19))
def test_ingestion_lambda_staff_deparment_data_saved_to_s3(
    get_credentials, pg_container_fixture, s3_fixture, caplog
):  # noqa E501
    """staff and deparment table data is saved to json"""
    s3_client, s3_bucket = s3_fixture
    test_conn = pg_container_fixture
    test_cursor = test_conn.cursor()

    # put last_update.txt run into a mock s3:
    s3_client.put_object(
        Body="2020:01:01:00:00:00",
        Bucket=s3_bucket,
        Key="last_update.txt",
    )

    # seed departments table
    test_cursor.execute(
        """INSERT INTO department
        (department_id, department_name, location, manager, created_at,last_updated)
        VALUES
        (1,'Department', 'Location', 'Manager', '2023-05-10 19:10:25.100', '2023-05-10 19:10:25.100');
        """  # noqa E501
    )
    # seed staff table
    test_cursor.execute(
        """INSERT INTO staff
        (staff_id, first_name, last_name, department_id, email_address, created_at, last_updated)
        VALUES
        (1, 'Test', 'Testy', 1, 'email@email.com','2100-05-10 19:10:25.100','2100-05-10 19:10:25.100');
        """  # noqa E501
    )
    test_conn.commit()

    # eventbridge scheduler invocation
    event = {"data_bucket_name": s3_bucket}

    with caplog.at_level(logging.INFO):
        lambda_handler(event, "context")
        assert "staff/2023/1/1/data-173019.json" in caplog.text  # noqa E501

    response = s3_client.list_objects(Bucket=s3_bucket)
    assert response["Contents"][1]["Key"] == "last_update.txt"  # noqa E501
    assert (
        response["Contents"][0]["Key"]
        == "department/2023/1/1/data-173019.json"  # noqa E501
    )


@patch(
    "src.ingestion_lambda.ingestion_lambda.get_credentials",
    return_value={
        "user": "testuser",
        "password": "testpass",
        "database": "testdb",
        "host": "localhost",
        "port": 5433,
    },
)
@time_machine.travel(dt(2023, 1, 1, 17, 30, 19))
def test_ingestion_lambda_counter_address_saved_to_s3(
    get_credentials, pg_container_fixture, s3_fixture, caplog
):  # noqa E501
    """counterparty and address table data saved to json"""
    s3_client, s3_bucket = s3_fixture
    test_conn = pg_container_fixture
    test_cursor = test_conn.cursor()

    # put last_update.txt run into a mock s3:
    s3_client.put_object(
        Body="2020:01:01:00:00:00",
        Bucket=s3_bucket,
        Key="last_update.txt",
    )

    # seed address table
    test_cursor.execute(
        """INSERT INTO address
        (address_id, address_line_1, address_line_2, district, city, postal_code, country, phone, created_at,last_updated)
        VALUES
        (1,'6826 Herzog Via', null, 'Avon', 'New Patienceburgh', '28441', 'Turkey', '1234', '2023-05-10 19:10:25.100', '2023-05-10 19:10:25.100');
        """  # noqa E501
    )
    # seed counterparty table
    test_cursor.execute(
        """INSERT INTO counterparty
        (counterparty_id, counterparty_legal_name, legal_address_id, commercial_contact, delivery_contact, created_at, last_updated)
        VALUES
        (1, 'Fahey and Sons',1, 'Micheal Toy', 'Mrs. Lucy Runolfsdottir','2100-05-10 19:10:25.100','2100-05-10 19:10:25.100');
        """  # noqa E501
    )
    test_conn.commit()

    # eventbridge scheduler invocation
    event = {"data_bucket_name": s3_bucket}

    with caplog.at_level(logging.INFO):
        lambda_handler(event, "context")
        assert "counterparty/2023/1/1/data-173019.json" in caplog.text  # noqa E501

    response = s3_client.list_objects(Bucket=s3_bucket)
    assert (
        response["Contents"][0]["Key"]
        == "address/2023/1/1/data-173019.json"  # noqa E501
    )

    assert (
        response["Contents"][1]["Key"]
        == "counterparty/2023/1/1/data-173019.json"  # noqa E501
    )
