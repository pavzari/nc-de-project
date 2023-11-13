from src.loading_lambda.loading_lambda import get_parquet
import logging
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


@mock_s3
class TestGetParquet:
    def test_returns_list_of_lists(self):
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket="test_bucket",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )  # noqa E501

        with open("test/mock_parquet/data-144511.parquet", mode="rb") as pq:
            s3.put_object(
                Body=pq.read(), Bucket="test_bucket", Key="data-144511.parquet"
            )

            assert get_parquet("test_bucket", "data-144511.parquet") == [
                (
                    1,
                    "Jeremie",
                    "Franey",
                    "Purchasing",
                    "Manchester",
                    "jeremie.franey@terrifictotes.com",
                ),
                (
                    2,
                    "Deron",
                    "Beier",
                    "Facilities",
                    "Manchester",
                    "deron.beier@terrifictotes.com",
                ),
                (
                    3,
                    "Jeanette",
                    "Erdman",
                    "Facilities",
                    "Manchester",
                    "jeanette.erdman@terrifictotes.com",
                ),
                (
                    4,
                    "Ana",
                    "Glover",
                    "Production",
                    "Leeds",
                    "ana.glover@terrifictotes.com",
                ),
                (
                    5,
                    "Magdalena",
                    "Zieme",
                    "HR",
                    "Leeds",
                    "magdalena.zieme@terrifictotes.com",
                ),
                (
                    6,
                    "Korey",
                    "Kreiger",
                    "Production",
                    "Leeds",
                    "korey.kreiger@terrifictotes.com",
                ),
                (
                    7,
                    "Raphael",
                    "Rippin",
                    "Purchasing",
                    "Manchester",
                    "raphael.rippin@terrifictotes.com",
                ),
                (
                    8,
                    "Oswaldo",
                    "Bergstrom",
                    "Communications",
                    "Leeds",
                    "oswaldo.bergstrom@terrifictotes.com",
                ),
                (
                    9,
                    "Brody",
                    "Ratke",
                    "Purchasing",
                    "Manchester",
                    "brody.ratke@terrifictotes.com",
                ),
                (
                    10,
                    "Jazmyn",
                    "Kuhn",
                    "Purchasing",
                    "Manchester",
                    "jazmyn.kuhn@terrifictotes.com",
                ),
                (
                    11,
                    "Meda",
                    "Cremin",
                    "Finance",
                    "Manchester",
                    "meda.cremin@terrifictotes.com",
                ),
                (
                    12,
                    "Imani",
                    "Walker",
                    "Finance",
                    "Manchester",
                    "imani.walker@terrifictotes.com",
                ),
                (
                    13,
                    "Stan",
                    "Lehner",
                    "Dispatch",
                    "Leds",
                    "stan.lehner@terrifictotes.com",
                ),
                (
                    14,
                    "Rigoberto",
                    "VonRueden",
                    "Communications",
                    "Leeds",
                    "rigoberto.vonrueden@terrifictotes.com",
                ),
                (
                    15,
                    "Tom",
                    "Gutkowski",
                    "Production",
                    "Leeds",
                    "tom.gutkowski@terrifictotes.com",
                ),
                (
                    16,
                    "Jett",
                    "Parisian",
                    "Facilities",
                    "Manchester",
                    "jett.parisian@terrifictotes.com",
                ),
                (
                    17,
                    "Irving",
                    'O"Keefe',
                    "Production",
                    "Leeds",
                    'irving.o"keefe@terrifictotes.com',
                ),
                (
                    18,
                    "Tomasa",
                    "Moore",
                    "HR",
                    "Leeds",
                    "tomasa.moore@terrifictotes.com",
                ),
                (
                    19,
                    "Pierre",
                    "Sauer",
                    "Purchasing",
                    "Manchester",
                    "pierre.sauer@terrifictotes.com",
                ),
                (
                    20,
                    "Flavio",
                    "Kulas",
                    "Production",
                    "Leeds",
                    "flavio.kulas@terrifictotes.com",
                ),
            ]

    def test_logs_ClientError_if_passed_a_bad_name(self, caplog):
        with caplog.at_level(logging.INFO):
            s3 = boto3.client("s3")
            s3.create_bucket(
                Bucket="test_bucket",
                CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
            )  # noqa E501

            with open(
                "test/mock_parquet/data-144511.parquet", mode="rb"
            ) as pq:  # noqa E501
                s3.put_object(
                    Body=pq.read(),
                    Bucket="test_bucket",
                    Key="data-144511.parquet",  # noqa E501
                )
            get_parquet("MyBucket", "data-144511.parquet")
            assert "The specified bucket does not exist" in caplog.text

    def test_logs_ClientError_if_passed_a_bad_key(self, caplog):
        with caplog.at_level(logging.INFO):
            s3 = boto3.client("s3")
            s3.create_bucket(
                Bucket="test_bucket",
                CreateBucketConfiguration={
                    "LocationConstraint": "eu-west-2"
                },  # noqa E501
            )

            with open(
                "test/mock_parquet/data-144511.parquet", mode="rb"
            ) as pq:  # noqa E501
                s3.put_object(
                    Body=pq.read(),
                    Bucket="test_bucket",
                    Key="data-144511.parquet",  # noqa E501
                )
            get_parquet("test_bucket", "spam-eggs")
            assert "The specified key does not exist" in caplog.text
