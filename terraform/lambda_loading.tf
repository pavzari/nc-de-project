resource "aws_lambda_function" "warehouse_loading_lambda" {
  function_name    = var.warehouse_loading_lambda
  handler          = "loading_lambda.lambda_handler"
  runtime          = "python3.11"
  timeout          = 900
  role             = aws_iam_role.role_for_warehouse_loading_lambda.arn
  s3_bucket        = aws_s3_bucket.lambda_code_bucket.id
  s3_key           = "loading_lambda/loading_lambda.zip"
  layers           = ["arn:aws:lambda:eu-west-2:336392948345:layer:AWSSDKPandas-Python311:2"]
  source_code_hash = resource.aws_s3_object.loading_lambda_code_upload.source_hash
}