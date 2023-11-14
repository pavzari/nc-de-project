from src.loading_lambda.loading_lambda import get_credentials
import os
import pytest
import boto3
from moto import mock_secretsmanager
import json
import logging

logger = logging.getLogger()


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@mock_secretsmanager
def test_ClientError_secret_that_does_not_exist(caplog):
    with caplog.at_level(logging.ERROR):
        get_credentials("not-a-real-secret")
        assert "Secret not-a-real-secret does not exist" in caplog.text


@mock_secretsmanager
def test_KeyError_with_missing_param(caplog):
    secret_string = {
        "host": "real host",
        "port": "definitely not a mock port",
        "password": "pa55word",
        "database": "database",
    }
    client = boto3.client("secretsmanager", region_name="eu-west-2")
    client.create_secret(Name="Mock", SecretString=json.dumps(secret_string))
    with caplog.at_level(logging.ERROR):
        get_credentials("Mock")
        assert "Missing key 'user' in database credentials."


@mock_secretsmanager
def test_connection_params_look_like_expected():
    secret_string = {
        "host": "real host",
        "port": "definitely not a mock port",
        "user": "real human",
        "password": "pa55word",
        "database": "database",
    }
    client = boto3.client("secretsmanager", region_name="eu-west-2")
    client.create_secret(Name="Mock", SecretString=json.dumps(secret_string))
    assert get_credentials("Mock") == {
        "host": "real host",
        "port": "definitely not a mock port",
        "user": "real human",
        "password": "pa55word",
        "database": "database",
    }
