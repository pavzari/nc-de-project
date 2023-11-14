resource "aws_iam_role" "role_for_warehouse_loading_lambda" {
  name = "role_for_warehouse_loading_lambda"
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "sts:AssumeRole"
        ],
        "Principal" : {
          "Service" : [
            "lambda.amazonaws.com"
          ]
        }
      }
    ]
  })
}

resource "aws_iam_policy" "cloudwatch_logs_policy_for_loading_lambda" {
  name        = "loading_lambda_cloudwatch_logs_policy"
  description = "Allows loading lambda to write logs to cloudwatch"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "logs:CreateLogGroup",
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.warehouse_loading_lambda}:*"
      }
    ]
  })
}

resource "aws_iam_policy" "warehouse_loading_lambda_s3_policy" {
  name        = "warehouse_loading_lambda_s3_policy"
  description = "Allows reading from tranformed data bucket."
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "s3:GetObject",
        Effect   = "Allow",
        Resource = "${aws_s3_bucket.transformed_data_bucket.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "loading_cw_policy_attachment" {
  policy_arn = aws_iam_policy.cloudwatch_logs_policy_for_loading_lambda.arn
  role       = aws_iam_role.role_for_warehouse_loading_lambda.name
}

resource "aws_iam_role_policy_attachment" "warehouse_loading_lambda_s3_policy_attachment" {
  role       = aws_iam_role.role_for_warehouse_loading_lambda.name
  policy_arn = aws_iam_policy.warehouse_loading_lambda_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "loading_lambda_secrets_manager_attachment" {
  policy_arn = aws_iam_policy.lambda_access_secrets_manager_policy.arn
  role       = aws_iam_role.role_for_warehouse_loading_lambda.name
}