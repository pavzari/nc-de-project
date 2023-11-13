import boto3
import logging
import json
import pandas as pd
from datetime import datetime as dt
from botocore.exceptions import ClientError
from pg8000 import Connection, DatabaseError, InterfaceError

logging.basicConfig()
logger = logging.getLogger("ingestion_lambda")
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler function for processing incoming events.

    Parameters
    ----------
    event : dict
        The event triggering the Lambda function.
    context : LambdaContext
        The runtime information of the Lambda function.

    Returns
    -------
    None

    Raises
    ------
    Exception
        If there is an error during the processing of the event.
    """
    invocation_time = dt.now()
    bucket_name = (
        "nc-de-project-ingested-data-bucket-20231102173127149000000003"  # noqa E501
    )
    secret_name = "production"

    try:
        credentials = get_credentials(secret_name)

        connection = get_connection(credentials)

        last_upload = get_last_upload(bucket_name)

        json_data = get_data(connection, last_upload)

        if json_data != {}:
            write_file(bucket_name, json_data, invocation_time)
        else:
            logger.info("No new updates to write to file")
    except Exception as e:
        logger.error(e)


def get_credentials(secret_name):
    """
    Gets credentials from the AWS Secrets Manager.

    Parameters
    ----------
    secret_name : str
        The name of the database credentials
        secret the lambda is trying to connect to.
        Options:
        - "totesys-production"
        - "totesys-warehouse"

    Raises
    ------
    ClientError
        If the secret name is not found in the Secrets Manager.
        If there is an unexpected error connecting to the Secrets Manager.
    KeyError
        If the credentials object has a missing key.

    Returns
    -------
    dict
        A dictionary containing the database connection credentials.
        Keys: host, port, user, password, database
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
    database_credentials : dict
        Database connection credentials containing
        user, host, database, port, password.

    Raises
    ------
    DatabaseError
        If there is an error connecting to the database.
    InterfaceError
        If there is an interface error.

    Returns
    -------
    Connection
        A successful pg8000 connection object.
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


def get_last_upload(bucket_name):
    """
    Retrieves the time the S3 bucket was last modified.

    Returns a datetime object that can be used in a PostgreSQL query.
    If no last update file exists, it returns a default datetime object.

    Parameters
    ----------
    bucket_name : str
        The name of the S3 bucket.

    Raises
    ------
    ClientError
        If there is an issue accessing the S3 bucket.

    Returns
    -------
    datetime.datetime
        A datetime object representing the last updated timestamp.
    """
    client = boto3.client("s3")

    try:
        response = client.get_object(Bucket=bucket_name, Key="last_update.txt")
        datetime_string = response["Body"].read().decode("utf-8")
        datetime_object = dt.strptime(datetime_string, "%Y:%m:%d:%H:%M:%S")
        logger.info("last updated datetime object returned")
        return datetime_object
    except ClientError as e:
        message = e.response["Error"]["Message"]
        if message == "The specified key does not exist.":
            dt_object = dt.strptime("2020:1:1:00:00:00", "%Y:%m:%d:%H:%M:%S")
            logger.info("default datetime object returned")
            return dt_object
        else:
            logger.error(e.response["Error"]["Message"])
    except Exception as e:
        logger.error(f"An unexpected error occurred {e}")


def get_data(conn, last_upload):
    """
    Gets data from the connected database from last_upload.

    Parameters
    ----------
    conn : Connection
        Database connection instance (pg8000 connect object).
    last_upload : datetime.datetime
        The timestamp of the last fetched data file.

    Returns
    -------
    dict
        JSON-formatted updated content.
    """
    try:
        updated_content = {}
        table_names = conn.run(
            """
                            SELECT table_name
                            FROM information_schema.tables
                            WHERE table_schema = 'public';
                            """
        )
        list_table_names = list(table_names)
        list_table_names.append(["all_addresses"])
        list_table_names.remove(["_prisma_migrations"])
        for table in list_table_names:
            if table[0] == "department":
                content = conn.run(
                    f"""
                                    SELECT * FROM {table[0]}
                                    """
                )
            elif table[0] == "all_addresses":
                content = conn.run(
                    """
                                    SELECT * FROM address
                                    """
                )
            # get updated content from other tables
            else:
                content = conn.run(
                    f"""
                                    SELECT * FROM {table[0]}
                                    WHERE (last_updated > :date)
                                    """,
                    date={last_upload.strftime("%Y-%m-%dT%H:%M:%S")},
                )

            # get all column names from the table
            if table[0] == "all_addresses":
                columns = conn.run(
                    """
                                    SELECT column_name
                                    FROM information_schema.columns
                                    WHERE table_schema='public'
                                    AND table_name= 'address'
                                    """
                )
            else:
                columns = conn.run(
                    f"""
                                    SELECT column_name
                                    FROM information_schema.columns
                                    WHERE table_schema='public'
                                    AND table_name= '{table[0]}'
                                    """
                )
            column_names = [name[0] for name in columns]
            # integrate column names and conn to the dataframe
            df = pd.DataFrame(content, columns=column_names)
            json_formatted = df.to_json(orient="records", date_format="iso")
            back_to_list = json.loads(json_formatted)
            if len(back_to_list) != 0:
                updated_content[table[0]] = back_to_list
        conn.close()
        if list(updated_content.keys()) == ["department", "all_addresses"]:
            updated_content = {}

        logger.info("Updated JSON content has been retrieved.")
        return updated_content
    except Exception as exc:
        logger.error(exc)
        raise exc


def write_file(bucket_name, json_data, timestamp=dt(2020, 1, 1, 0, 0, 0)):
    """
    Handles creation of a new data file in the S3 bucket.

    Saves the JSON file with a timestamp
    to organize the structure of S3 buckets.
    Overwrites a last_updated file with the
    time the handler was invoked.

    Parameters
    ----------
    bucket_name : str
        S3 bucket name.
    json_data : dict
        JSON data from the get_data utility (string).
    timestamp : datetime.datetime, optional
        Datetime object timestamp from the lambda handler when it is invoked.
        Default is January 1, 2020, 00:00:00.

    Raises
    ------
    ClientError
        Issue occurred regarding putting an object into the S3 bucket.
    """
    client = boto3.client("s3")
    date = dt.now()
    year = date.year
    month = date.month
    day = date.day
    time = date.strftime("%H%M%S")

    last_successful_timestamp = timestamp.strftime("%Y:%m:%d:%H:%M:%S")

    try:
        if json_data is None:
            raise Exception("No JSON data provided")

        if not isinstance(json_data, dict):
            raise Exception("Updated data type invalid. Dict expected.")

        for table in json_data:
            if table != "all_addresses":
                file_name = f"{table}/{year}/{month}/{day}/data-{time}.json"

                if table == "staff":
                    response = client.put_object(
                        Body=json.dumps(
                            {
                                table: json_data[table],
                                "department": json_data["department"],
                            }  # noqa E501
                        ),
                        Bucket=bucket_name,
                        Key=file_name,
                    )  # noqa E501
                    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                        logger.info(f"Success. File {file_name} saved.")

                elif table == "counterparty":
                    response = client.put_object(
                        Body=json.dumps(
                            {
                                table: json_data[table],
                                "address": json_data["all_addresses"],
                            }  # noqa E501
                        ),
                        Bucket=bucket_name,
                        Key=file_name,
                    )  # noqa E501
                    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                        logger.info(f"Success. File {file_name} saved.")

                else:
                    response = client.put_object(
                        Body=json.dumps({table: json_data[table]}),
                        Bucket=bucket_name,
                        Key=file_name,
                    )  # noqa E501
                    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                        logger.info(f"Success. File {file_name} saved.")

        datefileresponse = client.put_object(
            Body=last_successful_timestamp,
            Bucket=bucket_name,
            Key="last_update.txt",
        )
        if datefileresponse["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logger.info("Success. last_update.txt overwritten")
    except KeyError as e:
        logger.error(f" {e.response['Error']['Message']}")
    except ClientError as e:
        logger.error(f" {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(e)
