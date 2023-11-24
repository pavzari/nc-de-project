resource "aws_cloudwatch_log_group" "ingestion_lambda_log_group" {
  name = "/aws/lambda/${aws_lambda_function.ingestion_lambda.function_name}"
}

resource "aws_cloudwatch_log_group" "transformation_lambda_log_group" {
  name = "/aws/lambda/${aws_lambda_function.transformation_lambda.function_name}"
}

resource "aws_cloudwatch_log_group" "loading_lambda_log_group" {
  name = "/aws/lambda/${aws_lambda_function.warehouse_loading_lambda.function_name}"
}

resource "aws_sns_topic" "log_notification_topic" {
  name = "nc-de-project-pipeline-log-topic"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.log_notification_topic.arn
  protocol  = "email"
  endpoint  = "nc404namenotfound@gmail.com"
}

resource "aws_cloudwatch_log_metric_filter" "warning_metrics_filter_ingest" {
  name           = "ingestion-log-warning-filter"
  pattern        = "WARNING"
  log_group_name = aws_cloudwatch_log_group.ingestion_lambda_log_group.name

  metric_transformation {
    name      = "ingestion-warning-log-count"
    namespace = "IngestionMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "error_metric_filter_ingest" {
  name           = "ingestion-log-error-filter"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.ingestion_lambda_log_group.name

  metric_transformation {
    name      = "ingestion-error-log-count"
    namespace = "IngestionMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "runtime_error_ingest" {
  name           = "IngestionRuntimeError"
  pattern        = "RuntimeError"
  log_group_name = aws_cloudwatch_log_group.ingestion_lambda_log_group.name

  metric_transformation {
    name      = "ingestion-runtime-log-count"
    namespace = "IngestionMetrics"
    value     = "1"
  }
}


resource "aws_cloudwatch_metric_alarm" "error_alert_ingest" {
  alarm_name          = "ingestion-error"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.error_metric_filter_ingest.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.error_metric_filter_ingest.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "This metric monitors number of errors coming from the Ingestion Lambda in ten minute intervals"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]
}

resource "aws_cloudwatch_metric_alarm" "warning_alert_ingest" {
  alarm_name          = "ingestion-warning"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.warning_metrics_filter_ingest.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.warning_metrics_filter_ingest.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 2
  alarm_description   = "This metric monitors number of warnings coming from the Ingestion Lambda in ten minute intervals"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]

}

resource "aws_cloudwatch_metric_alarm" "runtime_alert_ingest" {
  alarm_name          = "IngestionRuntimeAlarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.runtime_error_ingest.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.runtime_error_ingest.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "This metric monitors for runtime errors"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]

}

resource "aws_cloudwatch_log_metric_filter" "warning_metrics_filter_transform" {
  name           = "transformation-log-warning-filter"
  pattern        = "WARNING"
  log_group_name = aws_cloudwatch_log_group.transformation_lambda_log_group.name


  metric_transformation {
    name      = "transformation-warning-log-count"
    namespace = "TransformMetrics"
    value     = "1"
  }
}
resource "aws_cloudwatch_log_metric_filter" "error_metric_filter_transform" {
  name           = "transformation-log-error-filter"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.transformation_lambda_log_group.name

  metric_transformation {
    name      = "transformation-error-log-count"
    namespace = "TransformMetrics"
    value     = "1"
  }
}
resource "aws_cloudwatch_log_metric_filter" "runtime_error_transform" {
  name           = "transformationRuntimeError"
  pattern        = "RuntimeError"
  log_group_name = aws_cloudwatch_log_group.transformation_lambda_log_group.name

  metric_transformation {
    name      = "transformation-runtime-log-count"
    namespace = "TransformMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "error_alert_transform" {
  alarm_name          = "transformation-error"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.error_metric_filter_transform.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.error_metric_filter_transform.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "This metric monitors number of errors coming from the Transformation Lambda in ten minute intervals"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]
}

resource "aws_cloudwatch_metric_alarm" "warning_alert_transform" {
  alarm_name          = "transformation-warning"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.warning_metrics_filter_transform.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.warning_metrics_filter_transform.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 2
  alarm_description   = "This metric monitors number of warnings coming from the Transformation Lambda in ten minute intervals"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]

}

resource "aws_cloudwatch_metric_alarm" "runtime_alert_transform" {
  alarm_name          = "transformationRuntimeAlarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.runtime_error_transform.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.runtime_error_transform.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "This metric monitors for runtime errors"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]

}

resource "aws_cloudwatch_log_metric_filter" "warning_metrics_filter_loading" {
  name           = "loading-log-warning-filter"
  pattern        = "WARNING"
  log_group_name = aws_cloudwatch_log_group.loading_lambda_log_group.name

  metric_transformation {
    name      = "loading-warning-log-count"
    namespace = "LoadingMetrics"
    value     = "1"
  }
}
resource "aws_cloudwatch_log_metric_filter" "error_metric_filter_loading" {
  name           = "loading-log-error-filter"
  pattern        = "ERROR"
  log_group_name = aws_cloudwatch_log_group.loading_lambda_log_group.name

  metric_transformation {
    name      = "loading-error-log-count"
    namespace = "LoadingMetrics"
    value     = "1"
  }
}
resource "aws_cloudwatch_log_metric_filter" "runtime_error_loading" {
  name           = "loadingRuntimeError"
  pattern        = "RuntimeError"
  log_group_name = aws_cloudwatch_log_group.loading_lambda_log_group.name

  metric_transformation {
    name      = "loadingruntime-log-count"
    namespace = "LoadingMetrics"
    value     = "1"
  }
}


resource "aws_cloudwatch_metric_alarm" "error_alert_loading" {
  alarm_name          = "loading-error"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.error_metric_filter_loading.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.error_metric_filter_loading.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "This metric monitors number of errors coming from the loading Lambda in ten minute intervals"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]
}

resource "aws_cloudwatch_metric_alarm" "warning_alert_loading" {
  alarm_name          = "loading-warning"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.warning_metrics_filter_loading.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.warning_metrics_filter_loading.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 2
  alarm_description   = "This metric monitors number of warnings coming from the loading Lambda in ten minute intervals"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]

}

resource "aws_cloudwatch_metric_alarm" "runtime_alert_loading" {
  alarm_name          = "loading-RuntimeAlarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.runtime_error_loading.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.runtime_error_loading.metric_transformation[0].namespace
  period              = 600
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "This metric monitors for runtime errors"
  alarm_actions       = [aws_sns_topic.log_notification_topic.arn]
}



