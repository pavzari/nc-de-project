resource "aws_lambda_function" "transformation_lambda" {
  function_name    = var.transformation_lambda
  handler          = "transformation_lambda.lambda_handler" 
  runtime          = "python3.11"
  timeout          = 900
  role             = aws_iam_role.role_for_transformation_lambda.arn
  s3_bucket        = aws_s3_bucket.lambda_code_bucket.id
  s3_key           = "transformation_lambda/transformation_lambda.zip"
  layers           = ["arn:aws:lambda:eu-west-2:336392948345:layer:AWSSDKPandas-Python311:2"]
  source_code_hash = resource.aws_s3_object.transformation_lambda_code_upload.source_hash
   environment {
    variables = {
      TRANS_BUCKET="${aws_s3_bucket.transformed_data_bucket.bucket}"
    }
  }
}