AWS Data Warehouse Pipeline
Installation and Initial Setup
Fork and Clone Repository:

Clone the main branch of the repository:

bash

git clone https://github.com/nc-de-project/nc-de-project.git

Install Required Modules:

Run the following command in the terminal:

bash

make requirements

Docker:

Download and install Docker from Docker's official website.
Run Initial Checks:

Execute the following command in the terminal:

bash

make run-checks

Secrets:

This pipeline relies on AWS Secrets Manager and GitHub secrets to secure credentials. No setup is required if working within this repository and project. For other databases or projects, set up secrets with appropriate credentials.

You are now set up and ready to use this pipeline.
How to Use This Project:
Ingestion Lambda:
Overview:

This AWS Lambda function processes incoming events, retrieves updated data from a database, and stores the formatted data in an S3 bucket to keep data up-to-date for data warehousing.
lambda_handler(event, context):

Parameters:

    event (dict): The event triggering the Lambda function.
    context (LambdaContext): The runtime information of the Lambda function.

Returns:

    None

Raises:

    Exception: If there is an error during the processing of the event.

Configuration:

    S3 Bucket:
    Ensure that the S3 bucket specified in the bucket_name variable exists and has the necessary permissions for the Lambda function to read and write data.
    Secrets Manager:
    Set the secret_name variable to the correct name of the AWS Secrets Manager secret containing the database credentials.

Dependencies:

    AWS Lambda
    AWS Secrets Manager
    AWS S3
    pg8000 (Python library for PostgreSQL)

Functionality:

    Get Database Credentials:
    Function: get_credentials(secret_name)
    Retrieves database connection credentials from AWS Secrets Manager.

    Establish Database Connection:
    Function: get_connection(database_credentials)
    Establishes a connection to the OLTP database using the provided credentials.

    Retrieve Last Upload Timestamp:
    Function: get_last_upload(bucket_name)
    Retrieves the timestamp of the last data upload from an S3 bucket.

    Retrieve Updated Data:
    Function: get_data(conn, last_upload)
    Fetches updated data from the connected database since the last upload timestamp.

    Write Data to S3:
    Function: write_file(bucket_name, json_data, timestamp=dt(2020, 1, 1, 0, 0, 0))
    Handles the creation of a new data file in the specified S3 bucket, organizing the structure by timestamp.

Transformation Lambda:
Overview:

This AWS Lambda function processes incoming events triggered by Amazon S3 events, reads JSON data from S3, transforms it according to predefined rules, and then writes the transformed data back to S3 in Parquet format.
Input:

    event: The event triggering the Lambda function. It is expected to contain information about the S3 object.
    context: The runtime information of the Lambda function.

Output:

    None

Exceptions:

    Exception: Raised if there is an error during the processing of the event.

Table Transformation Functions:

The Lambda function utilizes various functions to transform different types of tables.

    format_dim_location
    format_dim_staff
    format_dim_design
    format_dim_currency
    format_dim_counterparty
    format_dim_date
    format_fact_sales_order

Each of these functions formats relevant JSON data into a list of lists suitable for the corresponding table. If required data is missing or an unexpected error occurs, appropriate exceptions are raised.
Supporting Functions:

The Lambda function also includes several supporting functions:

    get_table_name: Extracts the table name from the S3 event.
    create_parquet_buffer: Converts formatted data into a Parquet file and stores it in an in-memory buffer.
    read_s3_json: Reads the JSON file from the S3 bucket, validates its format, and returns the content as a dictionary.
    get_object_path: Extracts the S3 bucket name and object key from the Records field of an event.
    get_content_from_file: Reads text from a specified file in an S3 bucket.
    write_file_to_s3: Writes a Parquet file to the transformed data bucket in Amazon S3.

Error Handling:

The Lambda function logs errors using the Python logger module. If an exception is raised during the processing of an event, an error message is logged, and the function continues to process subsequent events.
Dependencies:

    pandas: Used for data manipulation and creating Parquet files.
    boto3: The AWS SDK for Python, used for interacting with S3.

Note:

    The function assumes that the provided JSON data adheres to the expected structure for each table type.
    If an unexpected error occurs during processing, the Lambda function will log the error and continue with subsequent events.

Loading Lambda:
Overview:

This AWS Lambda function handles the insertion of Parquet data into an OLTP database (Totesys). It extracts data from Parquet files stored in an S3 bucket, transforms the data, and inserts it into the appropriate database table.
lambda_handler(event, context):

Parameters:

    event (dict): AWS Lambda event object containing information about the triggering S3 event.
    context (object): AWS Lambda runtime information.

Returns:

    None

Raises:

    DatabaseError: If a database error occurs during execution.
    InterfaceError: If an interface error occurs during execution.
    Exception: For any other unexpected exception.

Configuration:

    S3 Bucket:
    Ensure that the S3 bucket specified in the bucket_name variable exists and has the necessary permissions for the Lambda function to read Parquet files.
    Secrets Manager:
    Set the secret_name variable to the correct name of the AWS Secrets Manager secret containing the database credentials for the OLTP database (Totesys-warehouse).

Dependencies:

    AWS Lambda
    AWS Secrets Manager
    AWS S3
    Pandas (Python library for data manipulation)
    pg8000 (Python library for PostgreSQL)

Functionality:

    Extract Database Credentials:
    Function: get_credentials(secret_name)
    Retrieves database connection credentials from AWS Secrets Manager.

    Establish Database Connection:
    Function: get_connection(database_credentials)
    Establishes a connection to the OLTP database (Totesys-warehouse) using the provided credentials.

    Retrieve Parquet Data:
    Function: get_parquet(bucket_name, file_name)
    Extracts Parquet data from the specified S3 bucket and file.

    Retrieve Column Names:
    Function: get_column_names(conn, table_name)
    Retrieves the column names of the specified database table.

    Insert Data into Database:
    Function: lambda_handler(event, context)
    Inserts the extracted and transformed data into the appropriate database table based on the file trigger.

    Logging and Error Handling:
    The Lambda function logs events and errors using the logger object. Ensure that CloudWatch Logs are configured appropriately for your Lambda function.