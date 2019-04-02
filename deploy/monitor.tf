resource "aws_s3_bucket" "monitor_state_bucket" {
  bucket_prefix = "monitor-state-"
  acl = "private"
  force_destroy = true
}

resource "aws_lambda_function" "monitor_function" {
  function_name = "monitor-${element(keys(var.monitors), count.index)}"
  handler = "monitor.handle_call"
  runtime = "python3.7"
  role = "${aws_iam_role.lambda_monitor_role.*.arn[count.index]}"
  reserved_concurrent_executions = 1
  memory_size = 128
  timeout = "${var.monitor_execution_timeout}"

  filename = "${var.monitor_function_package}"
  source_code_hash = "${filebase64sha256(var.monitor_function_package)}"
  publish = true

  count = "${length(var.monitors)}"

  environment {
    variables {
      MON_TARGET_URL = "${element(values(var.monitors), count.index)}"
      MON_CWATCH_NAMESPACE = "${var.cwatch_namespace}"
      MON_CWATCH_METRIC_LATENCY = "${var.cwatch_latency_metric_name}"
      MON_CWATCH_METRIC_STATE = "${var.cwatch_state_metric_name}"
      MON_CWATCH_METRIC_HTTP_STATUS = "${var.cwatch_http_status_metric_name}"
      MON_RECEIVER_ARN = "${aws_sns_topic.notifications_topic.arn}"
      MON_STATE_BUCKET = "${aws_s3_bucket.monitor_state_bucket.id}"
      MON_REQUEST_TIMEOUT = "${var.http_request_timeout}"
    }
  }
}

resource "aws_cloudwatch_event_rule" "monitor_event" {
  name_prefix = "monitor-${element(keys(var.monitors), count.index)}-event-"
  schedule_expression = "rate(1 minute)"
  is_enabled = true
  description = "Event that executes the monitor for the URL ${element(values(var.monitors), count.index)}"
  count = "${length(var.monitors)}"
}

resource "aws_cloudwatch_event_target" "monitor_event_target" {
  rule = "${element(aws_cloudwatch_event_rule.monitor_event.*.name, count.index)}"
  arn = "${element(aws_lambda_function.monitor_function.*.arn, count.index)}:${element(aws_lambda_function.monitor_function.*.version, count.index)}"

  count = "${length(var.monitors)}"
}

resource "aws_lambda_permission" "monitor_call_permission" {
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.monitor_function.*.function_name[count.index]}"
  principal = "events.amazonaws.com"
  source_arn = "${aws_cloudwatch_event_rule.monitor_event.*.arn[count.index]}"
  qualifier = "${aws_lambda_function.monitor_function.*.version[count.index]}"
  count = "${length(var.monitors)}"
}
