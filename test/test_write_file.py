from src.ingestion_lambda.ingestion_lambda import write_file
from moto import mock_s3
from datetime import datetime as dt
import boto3
import pytest
import os
import time_machine
import logging

logger = logging.getLogger("MyLogger")
logger.setLevel(logging.INFO)


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@mock_s3
class TestWriteFile:
    """tests for write file util function"""

    def test_puts_json_file_and_updated_file_in_s3_bucket(self):
        testJSON = {"test": [{"name": "John"}, {"age": 30}, {"city": "New York"}]}
        timestamp = dt.now()
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket="TestBucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        write_file("TestBucket", testJSON, timestamp)

        response = s3.list_objects(Bucket="TestBucket")
        assert len(response["Contents"]) == 3

    @time_machine.travel(dt(2020, 1, 1, 17, 30, 19))
    def test_key_is_correct(self):
        testJSON = {"test": [{"name": "John"}, {"age": 30}, {"city": "New York"}]}
        timestamp = dt.now()
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket="TestBucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        write_file("TestBucket", testJSON, timestamp)

        response = s3.list_objects(Bucket="TestBucket")
        assert (
            response["Contents"][2]["Key"] == "test/2020/1/1/test-173019.json"
        )  # noqa E501

    @time_machine.travel(dt(2020, 1, 1, 17, 30, 19))
    def test_successful_log_output_is_correct(self, caplog):
        with caplog.at_level(logging.INFO):
            testJSON = {"test": [{"name": "John"}, {"age": 30}, {"city": "New York"}]}
            timestamp = dt.now()
            s3 = boto3.client("s3")
            s3.create_bucket(
                Bucket="TestBucket",
                CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
            )
            write_file("TestBucket", testJSON, timestamp)

            assert (
                "Success. File test/2020/1/1/test-173019.json saved."
                in caplog.text  # noqa: E501
            )  # noqa: E501

    def test_raises_client_error_if_invalid_bucket_name(self, caplog):
        with caplog.at_level(logging.ERROR):
            testJSON = {"name": "John", "age": 30, "city": "New York"}
            timestamp = dt.now()
            write_file("TestBucket", testJSON, timestamp)

            assert "The specified bucket does not exist" in caplog.text

    def test_raises_client_error_if_empty_json(self, caplog):
        with caplog.at_level(logging.ERROR):
            s3 = boto3.client("s3")
            s3.create_bucket(
                Bucket="TestBucket",
                CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
            )
            testJSON = None
            write_file("TestBucket", testJSON)

            assert "No JSON data provided" in caplog.text

    @time_machine.travel(dt(2020, 1, 1, 17, 30, 19))
    def test_writes_file_with_correct_time_stamp(self):
        testJSON = {"name": "John", "age": 30, "city": "New York"}
        timestamp = dt.now()
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket="TestBucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        write_file("TestBucket", testJSON, timestamp)
        response = s3.get_object(Bucket="TestBucket", Key="last_update.txt")
        text = response["Body"].read().decode("utf-8")

        assert text == "2020:01:01:17:30:19"

    def test_handles_key_error_if_json_not_provided(self, caplog):
        with caplog.at_level(logging.ERROR):
            testJSON = '{"name": "John", "age": 30, "city": "New York"}'
            timestamp = dt.now()
            write_file("TestBucket", testJSON, timestamp)

            assert "Updated data type invalid. Dict expected." in caplog.text
