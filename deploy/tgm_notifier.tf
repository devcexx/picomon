resource "aws_sns_topic" "notifications_topic" {
  name_prefix = "monitor-updates-"
}

resource "aws_sns_topic_subscription" "telegram_delivery_subscription" {
  topic_arn = "${aws_sns_topic.notifications_topic.arn}"
  protocol = "lambda"
  endpoint = "${aws_lambda_function.tgm_notifier_function.arn}:${aws_lambda_function.tgm_notifier_function.version}"
}

resource "aws_lambda_permission" "sns_telegram_notifier_permission" {
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.tgm_notifier_function.function_name}"
  principal = "sns.amazonaws.com"
  source_arn = "${aws_sns_topic.notifications_topic.arn}"
  qualifier = "${aws_lambda_function.tgm_notifier_function.version}"
}

output "sns_topic_arn" {
  value = "${aws_sns_topic.notifications_topic.arn}"
}

resource "aws_lambda_function" "tgm_notifier_function" {
  function_name = "monitor-telegram-notifier"
  handler = "tgmnotify.handle_call"
  runtime = "python3.7"
  role = "${aws_iam_role.lambda_tgm_notifier_role.arn}"
  memory_size = "128"
  timeout = "15"

  filename = "${var.telegram_notifier_package}"
  source_code_hash = "${filebase64sha256("${var.telegram_notifier_package}")}"
  publish = true

  environment {
    variables {
      NOTIFY_BOT_TOKEN = "${var.telegram_bot_token}"
      NOTIFY_TGM_CHATS = "${join(" ", "${var.telegram_receiver_chats}")}"
      NOTIFY_TGM_TITLE = "${var.telegram_message_title}"
    }
  }
}
