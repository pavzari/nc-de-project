resource "aws_iam_role" "role_for_ingestion_lambda" {
  name = "role_for_ingestion_lambda"
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

resource "aws_iam_policy" "cloudwatch_logs_policy_for_ingestion_lambda" {
  name        = "ingestion_lambda_cloudwatch_logs_policy"
  description = "Allows ingestion lambda to write logs to cloudwatch"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "logs:CreateLogGroup",
        Effect   = "Allow",
        Resource = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"]
      },
      {
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"],
        Effect   = "Allow",
        Resource = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.ingestion_lambda}:*"]
      }
    ]
  })
}

resource "aws_iam_policy" "ingestion_lambda_s3_ingestion_bucket_policy" {
  name   = "ingestion_lambda_s3_ingestion_bucket_policy"
  policy = data.aws_iam_policy_document.ingestion_lambda_s3_ingestion_bucket_document.json
}
resource "aws_iam_policy" "ingestion_lambda_s3_code_bucket_policy" {
  name   = "ingestion_lambda_s3_code_bucket_policy"
  policy = data.aws_iam_policy_document.ingestion_lambda_s3_code_bucket_document.json
}

data "aws_iam_policy_document" "ingestion_lambda_s3_code_bucket_document" {
  statement {
    effect = "Allow"


    actions = ["s3:GetObject"]

    resources = [
      "${aws_s3_bucket.lambda_code_bucket.arn}/*",
      "${aws_s3_bucket.lambda_code_bucket.arn}",
    ]
  }
}

data "aws_iam_policy_document" "ingestion_lambda_s3_ingestion_bucket_document" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3-object-lambda:GetObject",
      "s3-object-lambda:PutObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = [
      "${aws_s3_bucket.ingestion_data_bucket.arn}/*",
      "${aws_s3_bucket.ingestion_data_bucket.arn}",
    ]
  }
}

resource "aws_iam_policy" "lambda_access_secrets_manager_policy" {
  name        = "ingestion_lambda_secrets_manager_policy"
  description = "Policy that grants access to Secrets Manager for lambda"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "secretsmanager:GetSecretValue",
        Effect   = "Allow",
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingestion_lambda_rds_role_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSReadOnlyAccess"
  role       = aws_iam_role.role_for_ingestion_lambda.id
}


resource "aws_iam_role_policy_attachment" "ingestion_lambda_cw_role_attachment" {
  role       = aws_iam_role.role_for_ingestion_lambda.name
  policy_arn = aws_iam_policy.cloudwatch_logs_policy_for_ingestion_lambda.arn
}

resource "aws_iam_role_policy_attachment" "ingestion_lambda_s3_code_bucket_policy_attachment" {
  role       = aws_iam_role.role_for_ingestion_lambda.name
  policy_arn = aws_iam_policy.ingestion_lambda_s3_code_bucket_policy.arn
}

resource "aws_iam_role_policy_attachment" "ingestion_lambda_s3_ingestion_bucket_policy_attachment" {
  role       = aws_iam_role.role_for_ingestion_lambda.name
  policy_arn = aws_iam_policy.ingestion_lambda_s3_ingestion_bucket_policy.arn
}

resource "aws_iam_role_policy_attachment" "ingestion_lambda_secrets_manager_attachment" {
  policy_arn = aws_iam_policy.lambda_access_secrets_manager_policy.arn
  role       = aws_iam_role.role_for_ingestion_lambda.name
}
