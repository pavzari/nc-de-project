data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "archive_file" "ingestion_lambda_code_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/ingestion_lambda/ingestion_lambda.py"
  output_path = "${path.module}/../src/ingestion_lambda/ingestion_lambda.zip"
}

data "archive_file" "transformation_lambda_code_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/transformation_lambda/transformation_lambda.py"
  output_path = "${path.module}/../src/transformation_lambda/transformation_lambda.zip"
}

data "archive_file" "loading_lambda_code_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/loading_lambda/loading_lambda.py"
  output_path = "${path.module}/../src/loading_lambda/loading_lambda.zip"
}

resource "aws_s3_object" "ingestion_lambda_code_upload" {
  bucket      = aws_s3_bucket.lambda_code_bucket.id
  key         = "ingestion_lambda/ingestion_lambda.zip"
  source      = data.archive_file.ingestion_lambda_code_zip.output_path
  source_hash = filemd5(data.archive_file.ingestion_lambda_code_zip.output_path)
}

resource "aws_s3_object" "transformation_lambda_code_upload" {
  bucket      = aws_s3_bucket.lambda_code_bucket.id
  key         = "transformation_lambda/transformation_lambda.zip"
  source      = data.archive_file.transformation_lambda_code_zip.output_path
  source_hash = filemd5(data.archive_file.transformation_lambda_code_zip.output_path)
}

resource "aws_s3_object" "loading_lambda_code_upload" {
  bucket      = aws_s3_bucket.lambda_code_bucket.id
  key         = "loading_lambda/loading_lambda.zip"
  source      = data.archive_file.loading_lambda_code_zip.output_path
  source_hash = filemd5(data.archive_file.loading_lambda_code_zip.output_path)
}

