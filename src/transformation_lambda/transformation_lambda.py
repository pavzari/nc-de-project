import boto3
import io
import logging
import json
import pandas as pd
from datetime import datetime as dt
from botocore.exceptions import ClientError
import os

logging.basicConfig()
logger = logging.getLogger("transformation_lambda")
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

    # read "latest_json_data.txt" for a list of jsons
    # loop through the jsons:
    # - replace get_table_name with just extracting it from the s3 key/path
    # - extract json content (modify and reuse read_s3_json)
    # - decide on formatter
    # - modify write_file_to_s3 to return the key
    # - add the key to a list latest_parquet_data
    # - end of loop: write "latest_parquet_data.txt" to transformed bucket.

    # table_data_formatters = {
    #     "address": ("dim_location", format_dim_location),
    #     "staff": ("dim_staff", format_dim_staff),
    #     "design": ("dim_design", format_dim_design),
    #     "currency": ("dim_currency", format_dim_currency),
    #     "counterparty": ("dim_counterparty", format_dim_counterparty),
    #     "sales_order": [("dim_date", format_dim_date), / ("fact_sales_order", format_fact_sales_order)], # noqa E501
    # }

    # if table_name in table_data_formatters:
    #     mappings = table_data_formatters[table_name]

    #     if table_name == "sales_order":
    #         for olap_table, formatter in mappings:
    #             transformed_data = formatter(data)
    #             parquet_buffer = create_parquet_buffer(transformed_data)
    #             write_file_to_s3(bucket_name, olap_table, parquet_buffer)
    #     else:
    #         olap_table, formatter = mappings
    #         transformed_data = formatter(data)
    #         parquet_buffer = create_parquet_buffer(transformed_data)
    #         write_file_to_s3(bucket_name, olap_table, parquet_buffer)
    # else:
    #     logger.warning("Unrecognized JSON data received.")

    bucket_name = os.environ["TRANS_BUCKET"]

    table_name = get_table_name(event)
    data = read_s3_json(event)

    try:
        transformed_data = None
        OLAP_table_name = None

        if table_name == "address":
            transformed_data = format_dim_location(data)
            OLAP_table_name = "dim_location"
        elif table_name == "staff":
            transformed_data = format_dim_staff(data)
            OLAP_table_name = "dim_staff"
        elif table_name == "design":
            transformed_data = format_dim_design(data)
            OLAP_table_name = "dim_design"
        elif table_name == "currency":
            transformed_data = format_dim_currency(data)
            OLAP_table_name = "dim_currency"
        elif table_name == "counterparty":
            transformed_data = format_dim_counterparty(data)
            OLAP_table_name = "dim_counterparty"
        elif table_name == "sales_order":
            transformed_data = {
                "date": format_dim_date(data),
                "sales_order": format_fact_sales_order(data),
            }

        if transformed_data:
            if isinstance(transformed_data, dict):
                dp_buffer = create_parquet_buffer(transformed_data["date"])
                write_file_to_s3(bucket_name, "dim_date", dp_buffer)

                sp_buffer = create_parquet_buffer(
                    transformed_data["sales_order"]
                )  # noqa E501
                write_file_to_s3(bucket_name, "fact_sales_order", sp_buffer)

            else:
                parquet_buffer = create_parquet_buffer(transformed_data)
                write_file_to_s3(bucket_name, OLAP_table_name, parquet_buffer)
        else:
            logger.info(
                f"{table_name} JSON file received. No transformation required."
            )  # noqa E501
    except Exception as e:
        logger.error(f"Error whilst formatting JSON.{e}")


def get_table_name(event):
    """
    Extracts the table name to which the incoming JSON data belongs.

    Parameters
    ----------
    event : dict
        The event containing information about the incoming data.

    Returns
    -------
    str
        The extracted table name.
    """
    table_name = event["Records"][0]["s3"]["object"]["key"].split("/")[0]
    return table_name


def create_parquet_buffer(formatted_data):
    """
    Writes table-formatted data as Parquet to
    an in-memory buffer before uploading it to S3.

    Parameters
    ----------
    formatted_data : list or dict
        The data formatted for the table.

    Returns
    -------
    io.BytesIO
        A BytesIO buffer containing the Parquet data.

    Raises
    ------
    Exception
        If there is an error creating the Parquet buffer.
    """
    try:
        df = pd.DataFrame(formatted_data)
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer)
        return parquet_buffer
    except Exception as e:
        logging.error(f"Error creating parquet buffer: {e}")


def read_s3_json(event):
    """Handles S3 PutObject event
    read recent stored json file
    and convert to dictionary

    On receipt of a PutObject event, checks that the file type is json and
    then logs the contents.

    Args:
        event:
            a valid S3 PutObject event
        context:
            a valid AWS lambda Python context object - see
            https://docs.aws.amazon.com/lambda/latest/dg/python-context.html

    Return:
        dictionary formatted json content.

    Raises:
        RuntimeError: An unexpected error occurred in execution. Other errors
        result in an informative log message.
    """
    try:
        s3_bucket_name, s3_object_name = get_object_path(event["Records"])
        logger.info(f"Bucket is {s3_bucket_name}")
        logger.info(f"Object key is {s3_object_name}")

        if s3_object_name[-4:] != "json":
            raise InvalidFileTypeError

        s3 = boto3.client("s3")
        content = get_content_from_file(s3, s3_bucket_name, s3_object_name)
        dict_format_content = json.loads(content)
        logger.info("JSON content retrieved.")
        return dict_format_content
    except KeyError as k:
        logger.error(f"Error retrieving data, {k}")
    except ClientError as c:
        if c.response["Error"]["Code"] == "NoSuchKey":
            logger.error(f"No object found - {s3_object_name}")
        elif c.response["Error"]["Code"] == "NoSuchBucket":
            logger.error(f"No such bucket - {s3_bucket_name}")
        else:
            raise
    except UnicodeError:
        logger.error(f"File {s3_object_name} is not a valid json file")
    except InvalidFileTypeError:
        logger.error(f"File {s3_object_name} is not a valid json file")
    except Exception as e:
        logger.error(e)
        raise RuntimeError


def get_object_path(records):
    """
    Extracts bucket and object references from the Records field of an event.

    Parameters
    ----------
    records : list
        List of records containing S3 bucket and object information.

    Returns
    -------
    tuple
        A tuple containing the S3 bucket name and object key.
    """
    return (
        records[0]["s3"]["bucket"]["name"],
        records[0]["s3"]["object"]["key"],
    )  # noqa E501


def get_content_from_file(client, bucket, object_key):
    """
    Reads text from the specified file in an S3 bucket.

    Parameters
    ----------
    client
        An S3 client object.
    bucket : str
        The name of the S3 bucket.
    object_key : str
        The key of the object to be read.

    Returns
    -------
    str
        The text content of the file.
    """
    data = client.get_object(Bucket=bucket, Key=object_key)
    contents = data["Body"].read()
    return contents.decode("utf-8")


def write_file_to_s3(bucket_name, table_name, parquet_buffer):
    """
    Writes a Parquet file to the transformed data bucket in Amazon S3.

    Parameters
    ----------
    bucket_name : str
        The name of the S3 bucket.
    table_name : str
        The name of the table associated with the data.
    parquet_buffer : io.BytesIO
        A BytesIO buffer containing the Parquet data.

    Returns
    -------
    None

    Raises
    ------
    KeyError
        If there is an issue accessing the response metadata.
    ClientError
        If there is an error with the S3 client.
    Exception
        For any other unexpected exceptions.
    """
    client = boto3.client("s3")
    date = dt.now()
    year = date.year
    month = date.month
    day = date.day
    time = date.strftime("%H%M%S")

    file_name = (
        f"{table_name}/{year}/{month}/{day}/{table_name}-{time}.parquet"  # noqa E501
    )

    try:
        response = client.put_object(
            Body=parquet_buffer.getvalue(), Bucket=bucket_name, Key=file_name
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logger.info(f"Success. File {file_name} saved.")

    except KeyError as e:
        logger.error(f" {e.response['Error']['Message']}")
    except ClientError as e:
        logger.error(f" {e.response['Error']['Message']}")
    except Exception as e:
        logger.error(e)


def format_dim_location(address_json):
    """
    Formats the address data ready to be inserted
    into the dim_location table.

    Parameters
    ----------
        address_json: JSON, required.
            The JSON file to be transformed into parquet.

    Raises
    ------

    KeyError:
        If the address key is missing.
        If any of the columns are missing.

    Returns
    -------
        A list of lists.
    """
    dim_location = []
    try:
        addresses = address_json["address"]
        for address in addresses:
            insert = True
            row = [
                address["address_id"],
                address["address_line_1"],
                address["address_line_2"],
                address["district"],
                address["city"],
                address["postal_code"],
                address["country"],
                address["phone"],
            ]
            for list in dim_location:
                if list == row:
                    insert = False
            if insert is True:
                dim_location.append(row)
        return dim_location
    except KeyError as ke:
        logger.error(f"KeyError: missing key {ke}.")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")


def format_dim_staff(staff_data):
    """
    formats the data to populate the dim_staff table

    Parameters
    ----------
    json object containing the data from the staff table and department table.

    Raises
    ------
        AttributeError if data not in dictionary format
        KeyError if incorrect staff data provided
        Warning if a staff record cannot be formatted correctly

    Returns
    ------
    list of lists
        each list contains the staff_id, first_name,\
        last_name, department, location, email address

    """

    try:
        if "staff" not in staff_data.keys():
            raise KeyError("Incorrect staff data provided")

        staff = [x.copy() for x in staff_data["staff"]]
        department = [x.copy() for x in staff_data["department"]]

        for s in staff:
            for d in department:
                if s["department_id"] == d["department_id"]:
                    s["department"] = d["department_name"]
                    s["location"] = d["location"]

        for s in staff:
            if "department" not in s.keys():
                logger.warning(
                    f"staff_id {s['staff_id']}: no valid department_id "
                )  # noqa E501
                staff.remove(s)

        f_staff = [
            [
                s["staff_id"],
                s["first_name"],
                s["last_name"],
                s["department"],
                s["location"],
                s["email_address"],
            ]
            for s in staff
        ]

        logger.info("dim_staff data formatted sucessfully")
        return f_staff
    except KeyError as e:
        logger.error(f"{e}")
    except AttributeError as e:
        logger.error(f"{e}")
    except Exception as e:
        logger.error(f"An unexpected Error Occured: {e}")


def format_dim_design(design_table):
    """
    argument:design_table
        type:dict
            key: table name
            value: updated content (list of dictionary)

    return:
        type: list of list
            for each row:
                design_id: id (int)
                design_name:name of design (str)
                file_location:path of file (str)
                file_name:name of file (str)
    raise:
        RuntimeError
        KeyError

    """
    try:
        # read table content
        content = design_table["design"]

        # formatting
        result = []
        for row in content:
            result.append(
                {
                    "design_id": row["design_id"],
                    "design_name": row["design_name"],
                    "file_location": row["file_location"],
                    "file_name": row["file_name"],
                }
            )

        # transfer to list of list
        list_list = []
        for row in result:
            list_list.append(
                [
                    row["design_id"],
                    row["design_name"],
                    row["file_location"],
                    row["file_name"],
                ]
            )
        return list_list

    except KeyError as k:
        logger.error(f"Error retrieving data, {k}")

    except Exception as e:
        logger.error(e)
        raise RuntimeError


def format_dim_currency(currency_table):
    """
    Formats the ingested currency table into the correct format.

    Parameters
    ----------
    currency_table json

    Raises
    ------
    KeyError: Will return an error message, if the
        passed table has an incorrect key.
    RuntimeError: Returns an error when passed a wrong
        argument

    Returns
    -------
    A successful list of lists, containing a correctly formatted
    dim_currency table with the column names:
        currency_id
        currency_code
        currency_name
    """
    currency_name = {
        "GBP": "Pound Sterling",
        "USD": "United States dollar",
        "EUR": "Euros",
    }

    try:
        content = currency_table["currency"]

        all_currencies = []
        for row in content:
            all_currencies.append(
                {
                    "currency_id": row["currency_id"],
                    "currency_code": row["currency_code"],
                    "currency_name": currency_name[row["currency_code"]],
                }
            )

        list_of_list = []
        for row in all_currencies:
            list_of_list.append(
                [
                    row["currency_id"],
                    row["currency_code"],
                    row["currency_name"],
                ]
            )
        return list_of_list

    except KeyError as k:
        logger.error(f"Error retrieving data, {k}")

    except Exception as e:
        logger.error(e)
        raise RuntimeError


def format_dim_counterparty(table):
    """
    formats the data to populate the dim_staff table

    Parameters
    ----------
        json with data from the counterparty table and address table.

    Raises
    ------
    KeyError
        if incorrect counterpary data or address data provided
    RuntimeError
        if an unhandled exception occurs in the try block.

    Returns
    ------
    list of lists
        each list contains everything from the updated counterparty dict

    """

    try:
        # read counterparty table content from the ingestion lambda output
        updpated_cp = table["counterparty"]
        address_lookup = table["address"]
        cp_dict = []
        for cp in updpated_cp:
            # searching address from address_look_up_table
            address = [
                r
                for r in address_lookup
                if r["address_id"] == cp["legal_address_id"]  # noqa E501
            ][0]
            # formating the dim table
            cp_dict.append(
                {
                    "cp_id": cp["counterparty_id"],
                    "cp_legal_name": cp["counterparty_legal_name"],
                    "cp_legal_address_line_1": address["address_line_1"],
                    "cp_legal_address_line_2": address["address_line_2"],
                    "cp_legal_district": address["district"],
                    "cp_legal_city": address["city"],
                    "cp_legal_postal_code": address["postal_code"],
                    "cp_legal_country": address["country"],
                    "cp_legal_phone_number": address["phone"],
                }
            )

            list_of_lists = []
            for row in cp_dict:
                list_of_lists.append(
                    [
                        row["cp_id"],
                        row["cp_legal_name"],
                        row["cp_legal_address_line_1"],
                        row["cp_legal_address_line_1"],
                        row["cp_legal_district"],
                        row["cp_legal_city"],
                        row["cp_legal_postal_code"],
                        row["cp_legal_country"],
                        row["cp_legal_phone_number"],
                    ]
                )

        return list_of_lists

    except KeyError as k:
        logger.error(f"Error retrieving data, {k}")

    except Exception as e:
        logger.error(e)
        raise RuntimeError


def format_dim_date(sales_order_table):
    """
    argument:sales_order_table
        type:dict
            key: table name
            value: updated content (list of dictionary)

    return:
        type: list of list
            for each row:
                date_id:datetime (date ('%Y-%m-%d'))
                year:year of the date (int)
                month:month of the date (int)
                day:day of the date (int)
                day_of_week:weekday of date,0 for monday,6 for sunday(int)
                day_name:weekday name of the date (str)
                month_name: month name of the date (str)
                quarter: quarter of the date (int)
    raise:
        RuntimeError
        KeyError

    question:
        when running every 10mins if having sale_order
        and without accessing the data warehouse
        do we assert new line again and again for the same date?
        do we need to avoid it? how?

        im guessing the logic all done by loading lambda maybe
    """
    try:
        # read updated content from input table
        content = sales_order_table["sales_order"]

        # extract all date objects from table
        all_dates = []
        for row in content:
            all_dates += [
                dt.strptime(row["agreed_delivery_date"], "%Y-%m-%d"),
                dt.strptime(row["agreed_payment_date"], "%Y-%m-%d"),
                dt.strptime(row["created_at"][:10], "%Y-%m-%d"),
                dt.strptime(row["last_updated"][:10], "%Y-%m-%d"),
            ]

        # remove the duplicate date
        remove_duplicate = list(set(all_dates))

        # formatting
        result = []
        for date in remove_duplicate:
            result.append(
                {
                    "date_id": date.strftime("%Y-%m-%d"),
                    "year": date.year,
                    "month": date.month,
                    "day": date.day,
                    "day_of_week": date.weekday() + 1,
                    "day_name": date.strftime("%A"),
                    "month_name": date.strftime("%B"),
                    "quarter": 1 + (date.month - 1) // 3,
                }
            )

        # transfer to list of list
        list_list = []
        for row in result:
            list_list.append(
                [
                    row["date_id"],
                    row["year"],
                    row["month"],
                    row["day"],
                    row["day_of_week"],
                    row["day_name"],
                    row["month_name"],
                    row["quarter"],
                ]
            )
        return list_list

    except KeyError as k:
        logger.error(f"Error retrieving data, {k}")

    except Exception as e:
        logger.error(e)
        raise RuntimeError


def format_fact_sales_order(sales_order_json):
    """
    Formats the sales_order data ready to be inserted
    into the fact_sales_order table.

    Parameters
    ----------
        sales_order_json: JSON, required.
            The JSON file to be transformed into parquet.

    Raises
    ------

    KeyError:
        If the sales_order key is missing.
        If any of the columns are missing.

    Returns
    -------
        A list of lists.
    """
    sales_order_parquet = []
    try:
        json = sales_order_json["sales_order"]
        for sale in json:
            insert = True
            created_date = sale["created_at"][:10]
            created_time = sale["created_at"][11:19]
            last_updated_date = sale["last_updated"][:10]
            last_updated_time = sale["last_updated"][11:19]
            row = [
                sale["sales_order_id"],
                created_date,
                created_time,
                last_updated_date,
                last_updated_time,
                sale["staff_id"],
                sale["counterparty_id"],
                sale["units_sold"],
                sale["unit_price"],
                sale["currency_id"],
                sale["design_id"],
                sale["agreed_payment_date"],
                sale["agreed_delivery_date"],
                sale["agreed_delivery_location_id"],
            ]
            for list in sales_order_parquet:
                if list == row:
                    insert = False
            if insert is True:
                sales_order_parquet.append(row)
        return sales_order_parquet
    except KeyError as ke:
        logger.error(f"KeyError: missing key {ke}.")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")


class InvalidFileTypeError(Exception):
    """Traps error where file type is not json."""

    pass
