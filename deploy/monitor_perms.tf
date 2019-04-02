data "aws_iam_policy_document" "lambda_monitor_assume_role_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type = "Service"
      identifiers = [ "lambda.amazonaws.com" ]
    }
  }
}

data "aws_iam_policy_document" "lambda_monitor_role_policy" {
  statement {
    effect = "Allow"
    
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]

    resources = [ "*" ]
  }

  statement {
    effect = "Allow"
    actions = [
      "cloudwatch:PutMetricData"
    ]

    resources = [ "*" ]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "sns:*"
    ]
    resources = [ "*" ]
  }
}

resource "aws_iam_role" "lambda_monitor_role" {
  name_prefix = "mon-${element(keys(var.monitors), count.index)}-role-"
  assume_role_policy = "${data.aws_iam_policy_document.lambda_monitor_assume_role_policy.json}"

  count = "${length(var.monitors)}"
}

resource "aws_iam_role_policy" "lambda_monitor_policy" {
  role = "${aws_iam_role.lambda_monitor_role.*.name[count.index]}"
  policy = "${data.aws_iam_policy_document.lambda_monitor_role_policy.json}"

  count = "${length(var.monitors)}"
}
