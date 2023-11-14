resource "aws_s3_bucket" "lambda_code_bucket" {
  bucket_prefix = "nc-de-project-lambda-code-bucket-"
}

resource "aws_s3_bucket" "ingestion_data_bucket" {
  bucket_prefix = "nc-de-project-ingested-data-bucket-"
}

resource "aws_s3_bucket" "transformed_data_bucket" {
  bucket_prefix = "nc-de-project-transformed-data-"
}

resource "aws_s3_bucket_notification" "ingestion_bucket_notification" {
  bucket = aws_s3_bucket.ingestion_data_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.transformation_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = "latest_json_data.txt"
  }
  depends_on = [aws_lambda_permission.tranformation_lambda_invoke_permission]
}

resource "aws_lambda_permission" "tranformation_lambda_invoke_permission" {
  statement_id  = "AllowS3Invocation"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transformation_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.ingestion_data_bucket.arn
}

resource "aws_s3_bucket_notification" "tranformed_bucket_notification" {
  bucket = aws_s3_bucket.transformed_data_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.warehouse_loading_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = "latest_parquet_data.txt"
  }
  depends_on = [aws_lambda_permission.loading_lambda_invoke_permission]
}

resource "aws_lambda_permission" "loading_lambda_invoke_permission" {
  statement_id  = "AllowS3Invocation"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.warehouse_loading_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.transformed_data_bucket.arn
}

