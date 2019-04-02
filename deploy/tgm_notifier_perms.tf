data "aws_iam_policy_document" "lambda_tgm_notifier_assume_role_policy" {
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

data "aws_iam_policy_document" "lambda_tgm_notifier_role_policy" {
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
}

resource "aws_iam_role" "lambda_tgm_notifier_role" {
  name_prefix = "monitor-tgm-notifier-role-"
  assume_role_policy = "${data.aws_iam_policy_document.lambda_tgm_notifier_assume_role_policy.json}"
}

resource "aws_iam_role_policy" "lambda_tgm_notifier_policy" {
  role = "${aws_iam_role.lambda_tgm_notifier_role.name}"
  policy = "${data.aws_iam_policy_document.lambda_tgm_notifier_role_policy.json}"
}
