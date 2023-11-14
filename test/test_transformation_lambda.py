from src.transformation_lambda.transformation_lambda import lambda_handler
import time_machine
from datetime import datetime as dt
import logging
from unittest.mock import patch
from moto import mock_s3
import boto3
import pytest
import os

logger = logging.getLogger("MyLogger")
logger.setLevel(logging.INFO)


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"

@patch.dict(os.environ,{"TRANS_BUCKET":"mocked_bucket_name"})# noqa E501
@mock_s3
class TestTransformationLambda:
    """tests for transformation lambda"""

    # design

    @patch(
        "src.transformation_lambda.transformation_lambda.read_s3_json",
        return_value={
            "design": [
                {
                    "design_id": 8,
                    "created_at": "2022-11-03T14:20:49.962",
                    "design_name": "Wooden",
                    "file_location": "/usr",
                    "file_name": "wooden-20220717-npgz.json",
                    "last_updated": "2022-11-03T14:20:49.962",
                }
            ]
        },
    )
    @patch(
        "src.transformation_lambda.transformation_lambda.get_table_name",
        return_value="design",
    )
    @time_machine.travel(dt(2020, 1, 1, 17, 30, 19))
    def test_creates_design_parquet_file(self, read_s3_json, get_table_name):
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket="mocked_bucket_name",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )  # noqa E501

        lambda_handler("event", "context")

        response = s3.list_objects(
            Bucket="mocked_bucket_name"
        )  # noqa E501
        assert (
            response["Contents"][0]["Key"]
            == "dim_design/2020/1/1/data-173019.parquet"  # noqa E501
        )

    # sales_order

    @patch(
        "src.transformation_lambda.transformation_lambda.read_s3_json",
        return_value={
            "sales_order": [
                {
                    "sales_order_id": 1,
                    "created_at": "2022-11-03T14:20:52.186",
                    "last_updated": "2022-11-03T14:20:52.186",
                    "design_id": 9,
                    "staff_id": 16,
                    "counterparty_id": 18,
                    "units_sold": 84754,
                    "unit_price": 2.43,
                    "currency_id": 3,
                    "agreed_delivery_date": "2022-11-10",
                    "agreed_payment_date": "2022-11-03",
                    "agreed_delivery_location_id": 4,
                }
            ]
        },
    )
    @patch(
        "src.transformation_lambda.transformation_lambda.get_table_name",
        return_value="sales_order",
    )
    @time_machine.travel(dt(2020, 1, 1, 17, 30, 19))
    def test_creates_sales_order_and_date_parquet_files(
        self, read_s3_json, get_table_name
    ):
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket="mocked_bucket_name",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        lambda_handler("event", "context")

        response = s3.list_objects(
            Bucket="mocked_bucket_name"
        )
        assert (
            response["Contents"][0]["Key"]
            == "dim_date/2020/1/1/data-173019.parquet"  # noqa E501
        )
        assert (
            response["Contents"][1]["Key"]
            == "fact_sales_order/2020/1/1/data-173019.parquet"
        )  # noqa E501

    # staff

    @patch(
        "src.transformation_lambda.transformation_lambda.read_s3_json",
        return_value={
            "staff": [
                {
                    "staff_id": 1,
                    "first_name": "Jeremie",
                    "last_name": "Franey",
                    "department_id": 2,
                    "email_address": "jeremie.franey@terrifictotes.com",
                    "created_at": "2022-11-03T14:20:51.563",
                    "last_updated": "2022-11-03T14:20:51.563",
                },
                {
                    "staff_id": 1,
                    "first_name": "Jeremie",
                    "last_name": "Franey",
                    "department_id": 1,
                    "email_address": "jeremie.franey@terrifictotes.com",
                    "created_at": "2022-11-03T14:20:51.563",
                    "last_updated": "2022-11-03T14:20:51.563",
                },
            ],
            "department": [
                {
                    "department_id": 2,
                    "department_name": "Purchasing",
                    "location": "Manchester",
                    "manager": "Naomi Lapaglia",
                    "created_at": "2022-11-03T14:20:49.962",
                    "last_updated": "2022-11-03T14:20:49.962",
                }
            ],
        },
    )
    @patch(
        "src.transformation_lambda.transformation_lambda.get_table_name",
        return_value="staff",
    )
    @time_machine.travel(dt(2020, 1, 1, 17, 30, 19))
    def test_creates_dim_staff_parquet(self, read_s3_json, get_table_name):
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket="mocked_bucket_name",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        lambda_handler("event", "context")

        response = s3.list_objects(
            Bucket="mocked_bucket_name"
        )
        assert (
            response["Contents"][0]["Key"]
            == "dim_staff/2020/1/1/data-173019.parquet"  # noqa E501
        )

    # department

    @patch(
        "src.transformation_lambda.transformation_lambda.read_s3_json",
        return_value={
            "department": [
                {
                    "department_id": 2,
                    "department_name": "Purchasing",
                    "location": "Manchester",
                    "manager": "Naomi Lapaglia",
                    "created_at": "2022-11-03T14:20:49.962",
                    "last_updated": "2022-11-03T14:20:49.962",
                }
            ],
        },
    )
    @patch(
        "src.transformation_lambda.transformation_lambda.get_table_name",
        return_value="department",
    )
    @time_machine.travel(dt(2020, 1, 1, 17, 30, 19))
    def test_ignores_department_json(self, read_s3_json, get_table_name):
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket="mocked_bucket_name",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )

        lambda_handler("event", "context")

        response = s3.list_objects(
            Bucket="mocked_bucket_name"
        )

        assert "Contents" not in response.keys()

    def test_error_if_lambda_triggered_not_by_json(self, caplog):
        with caplog.at_level(logging.INFO):
            test_event = {
                "Records": [
                    {
                        "eventVersion": "2.1",
                        "eventSource": "aws:s3",
                        "awsRegion": "eu-west-2",
                        "eventTime": "2023-11-03T11:11:19.251Z",
                        "eventName": "ObjectCreated:Put",
                        "userIdentity": {"principalId": "testId"},
                        "requestParameters": {"sourceIPAddress": "test_ip"},
                        "responseElements": {
                            "x-amz-request-id": "test_id",
                            "x-amz-id-2": "test_id",
                        },
                        "s3": {
                            "s3SchemaVersion": "1.0",
                            "configurationId": "bucket_upload_something",
                            "bucket": {
                                "name": "test_bucket_name",
                                "ownerIdentity": {"principalId": "testId"},
                                "arn": "test_arn",
                            },
                            "object": {
                                "key": "some_random_file.txt",
                                "size": 0,
                                "eTag": "test_eTag",
                                "sequencer": "test_sequencer",
                            },
                        },
                    }
                ]
            }

            lambda_handler(test_event, "context")
            assert (
                "File some_random_file.txt is not a valid json file"
                in caplog.text  # noqa E501
            )
