import time
import pandas as pd
from pg8000 import Connection, DatabaseError, InterfaceError
import json
import boto3
import logging
from botocore.exceptions import ClientError
from io import BytesIO

logging.basicConfig()
logger = logging.getLogger("loading_lambda")
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Handles Lambda function execution.

    Parameters
    ----------
    event : dict
        AWS Lambda event object containing
        information about the triggering event.
    context : object
        AWS Lambda runtime information.

    Raises
    ------
    DatabaseError
        If a database error occurs.
    InterfaceError
        If an interface error occurs.
    Exception
        For any other unexpected exception.

    Returns
    -------
    None
    """
    try:
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"]
        table_name = key.split("/")[0]

        credentials = get_credentials("warehouse")
        conn = get_connection(credentials)

        data = get_parquet(bucket_name, key)

        column_names = get_column_names(conn, table_name)

        if table_name == "fact_sales_order":
            time.sleep(20)
            for record in data:
                list_columns = list(column_names)
                list_columns.remove("sales_record_id")
                string_columns = ", ".join(list_columns)
                conn.run(
                    f"""
                                    INSERT INTO {table_name}
                                    ({string_columns})
                                    VALUES {record};
                                    """.replace(
                        '"', "''"
                    ).replace(
                        "None", "NULL"
                    )
                )
                conn.commit()
        elif table_name == "dim_date":
            for record in data:
                list_columns = list(column_names)
                string_columns = ", ".join(list_columns)
                conn.run(
                    f"""
                                    INSERT INTO {table_name}
                                    VALUES {record}
                                    ON CONFLICT (date_id) DO NOTHING;
                                    """.replace(
                        '"', "''"
                    ).replace(
                        "None", "NULL"
                    )
                )
                conn.commit()
        else:
            for record in data:
                list_columns = list(column_names)
                string_columns = ", ".join(list_columns)
                conn.run(
                    f"""
                                    INSERT INTO {table_name}
                                    VALUES {record};
                                    """.replace(
                        '"', "''"
                    ).replace(
                        "None", "NULL"
                    )
                )
                conn.commit()
        conn.close()

        logger.info(f"data successfully inserted into {table_name}")

    except DatabaseError as db:
        logger.error(f"pg8000 - an error has occurred: {db.args[0]['M']}")
    except Exception as exc:
        logger.error(exc)


def get_credentials(secret_name):
    """
    Gets credentials from the AWS secrets manager.

    Parameters
    ----------
    secret_name : str
        The name of the database credentials secret
        the lambda is trying to connect to.
        Options: "totesys-production", "totesys-warehouse".

    Raises
    ------
    ClientError
        If the secret name is not found in the secrets manager.
        If there is an unexpected error connecting to the secrets manager.
    KeyError
        If the credentials object has a missing key.

    Returns
    -------
    dict
        A json-like object that contains the database connection credentials
        that can be accessed using the following keys:
        host, port, user, password, database
    """
    try:
        client = boto3.client("secretsmanager", region_name="eu-west-2")
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])

        connection_params = {
            "host": secret["host"],
            "port": secret["port"],
            "user": secret["user"],
            "password": secret["password"],
            "database": secret["database"],
        }
        logger.info("connection parameters returned")
        return connection_params

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            logger.error(f"Secret {secret_name} does not exist.")
        else:
            logger.error(f"Error accessing database secret {secret_name}: {e}")
    except KeyError as e:
        logger.error(f"Missing key {e} in database credentials.")


def get_connection(database_credentials):
    """
    Gets connections to the OLTP database - Totesys.


    Parameters
    ----------
    database_credentials (from the get_credentials util),
    which is a dictionary consisting of:
        user
        host
        database
        port
        password

    Raises
    ------
    DatabaseError: Will return an error message showing what is missing.
        i.e. if the password is wrong, the error message will state password
        authentication has failed.
    InterfaceError:

    Returns
    -------
    A successful pg8000 connection object will be returned.
    """
    try:
        user = database_credentials["user"]
        host = database_credentials["host"]
        database = database_credentials["database"]
        port = database_credentials["port"]
        password = database_credentials["password"]
        conn = Connection(user, host, database, port, password, timeout=5)
        logger.info("Connection to database Totesys has been established.")
        return conn
    except DatabaseError as db:
        logger.error(f"pg8000 - an error has occurred: {db.args[0]['M']}")
        raise db
    except InterfaceError as ie:
        logger.error(f'pg8000 - an error has occurred: \n"{ie}"')
        raise ie
    except Exception as exc:
        logger.error(
            "An error has occurred when \
            attempting to connect to the database."
        )
        raise exc


def get_parquet(bucket_name, file_name):
    """
    Extracts the parquet file and returns the values
    of the rows in a list of tuples.

    Parameters
    ----------
    bucket_name : str
        The name of the bucket containing the parquet files.
    file_name : str
        The name of the file triggering the lambda.

    Returns
    -------
    list
        A list of tuples representing the values of each row.
    """
    client = boto3.client("s3")
    try:
        response = client.get_object(Bucket=bucket_name, Key=file_name)
        restored_df = pd.read_parquet(BytesIO(response["Body"].read()))
        formatted_df = restored_df.replace(
            to_replace=r"'", value='"', regex=True
        )  # noqa E501
        values = formatted_df.values.tolist()

        list_of_tuples = [tuple(list) for list in values]

        return list_of_tuples
    except ClientError as e:
        logger.error(e.response["Error"]["Message"])
    except Exception as e:
        logger.error(f"An unexpected error occurred {e}")


def get_column_names(conn, table_name):
    """
    Gets all columns name of the given table.

    Parameters
    ----------
    conn : Connection
        Database connection instance.
    table_name : str
        Table name.

    Returns
    -------
    str
        A string of column names: "(column, column, column)".
    """
    try:
        columns = conn.run(
            f"""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name= '{table_name}'
                            """
        )

        result = tuple([name[0] for name in columns])
        if len(result) <= 2:
            raise DatabaseError("Incorrect table name has been provided.")
        logger.info(f"Column names returned are: {result}")
        return result
    except (DatabaseError, InterfaceError) as e:
        logger.error(f"pg8000 - an error has occurred: {e}")
    except Exception as exc:
        logger.error(exc)
        raise exc
