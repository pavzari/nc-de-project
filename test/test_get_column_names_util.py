from src.loading_lambda.loading_lambda import get_column_names
import logging
import subprocess
import os
import pytest
import time
import pg8000

logger = logging.getLogger("MyLogger")
logger.setLevel(logging.INFO)


@pytest.fixture(scope="module")
def pg_container_fixture():
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
        conn = pg8000.connect(
            user="testuser",
            password="testpass",
            host="localhost",
            port=5433,
            database="testdb",
        )
        yield conn
    finally:
        conn.close()
        subprocess.run(
            ["docker", "compose", "-f", compose_path, "down"], check=False
        )  # noqa: E501


def test_real_dim_counterparty_columns(pg_container_fixture):
    conn = pg_container_fixture
    result = get_column_names(conn, "dim_counterparty")
    assert result == (
        "counterparty_id",
        "counterparty_legal_name",
        "counterparty_legal_address_line_1",
        "counterparty_legal_address_line_2",
        "counterparty_legal_district",
        "counterparty_legal_city",
        "counterparty_legal_postal_code",
        "counterparty_legal_country",
        "counterparty_legal_phone_number",
    )  # noqa E501


def test_real_dim_currency_columns(pg_container_fixture):
    conn = pg_container_fixture
    result = get_column_names(conn, "dim_currency")
    assert result == ("currency_id", "currency_code", "currency_name")


def test_real_dim_design_columns(pg_container_fixture):
    conn = pg_container_fixture
    result = get_column_names(conn, "dim_design")
    assert result == (
        "design_id",
        "design_name",
        "file_location",
        "file_name",
    )  # noqa E501


def test_real_dim_location_columns(pg_container_fixture):
    conn = pg_container_fixture
    result = get_column_names(conn, "dim_location")
    assert result == (
        "location_id",
        "address_line_1",
        "address_line_2",
        "district",
        "city",
        "postal_code",
        "country",
        "phone",
    )  # noqa E501


def test_real_dim_staff_columns(pg_container_fixture):
    conn = pg_container_fixture
    result = get_column_names(conn, "dim_staff")
    assert result == (
        "staff_id",
        "first_name",
        "last_name",
        "department_name",
        "location",
        "email_address",
    )  # noqa E501


def test_real_fact_sales_order_columns(pg_container_fixture):
    conn = pg_container_fixture
    result = get_column_names(conn, "fact_sales_order")
    assert result == (
        "sales_record_id",
        "sales_order_id",
        "created_date",
        "created_time",
        "last_updated_date",
        "last_updated_time",
        "sales_staff_id",
        "counterparty_id",
        "units_sold",
        "unit_price",
        "currency_id",
        "design_id",
        "agreed_payment_date",
        "agreed_delivery_date",
        "agreed_delivery_location_id",
    )  # noqa E501


def test_real_dim_currency_columns_incorrect_table_name(
    pg_container_fixture, caplog
):  # noqa E501
    with caplog.at_level(logging.INFO):
        conn = pg_container_fixture
        get_column_names(conn, "wrong_table_name")
        assert "Incorrect table name has been provided." in caplog.text
