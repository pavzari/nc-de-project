resource "aws_lambda_function" "ingestion_lambda" {
  function_name    = var.ingestion_lambda
  handler          = "ingestion_lambda.lambda_handler"
  runtime          = "python3.11"
  timeout          = 900
  role             = aws_iam_role.role_for_ingestion_lambda.arn
  s3_bucket        = aws_s3_bucket.lambda_code_bucket.id
  s3_key           = "ingestion_lambda/ingestion_lambda.zip"
  layers           = ["arn:aws:lambda:eu-west-2:336392948345:layer:AWSSDKPandas-Python311:2"]
  source_code_hash = resource.aws_s3_object.ingestion_lambda_code_upload.source_hash
}

