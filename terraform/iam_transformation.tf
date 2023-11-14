resource "aws_iam_role" "role_for_transformation_lambda" {
  name = "role_for_transformation_lambda"
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

resource "aws_iam_policy" "cloudwatch_logs_policy_for_transformation_lambda" {
  name        = "transformation_lambda_cloudwatch_logs_policy"
  description = "Allows transformation lambda to write logs to cloudwatch"
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
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.transformation_lambda}:*"
      }
    ]
  })
}

resource "aws_iam_policy" "transformation_lambda_s3_policy" {
  name        = "transformation_lambda_s3_policy"
  description = "Allows reading from  ingested data bucket and writing to transformed data bucket"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3-object-lambda:GetObject",
          "s3-object-lambda:PutObject",
          "s3:ListBucket"
        ],
        Effect = "Allow",
        Resource = [
          "${aws_s3_bucket.ingestion_data_bucket.arn}/*",
          "${aws_s3_bucket.ingestion_data_bucket.arn}"
        ]
      },
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3-object-lambda:GetObject",
          "s3-object-lambda:PutObject",
          "s3:ListBucket"
        ],
        Effect = "Allow",
        Resource = [
          "${aws_s3_bucket.transformed_data_bucket.arn}/*",
          "${aws_s3_bucket.transformed_data_bucket.arn}",
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "transformation_lambda_cw_policy_attachment" {
  policy_arn = aws_iam_policy.cloudwatch_logs_policy_for_transformation_lambda.arn
  role       = aws_iam_role.role_for_transformation_lambda.name
}

resource "aws_iam_role_policy_attachment" "transformation_lambda_s3_policy_attachment" {
  role       = aws_iam_role.role_for_transformation_lambda.name
  policy_arn = aws_iam_policy.transformation_lambda_s3_policy.arn
}