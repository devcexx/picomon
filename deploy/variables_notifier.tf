variable "telegram_notifier_package" {
  type = "string"
  description = "The path of a zip that contains a prepared distribution of the telegram notifier function"
}

variable "telegram_receiver_chats" {
  type = "list"
  description = "A list that contains the different Telegram chat ids of the recipients that will receive the notifications"
}

variable "telegram_bot_token" {
  type = "string"
  description = "The Telegram bot token"
}

variable "telegram_message_title" {
  type = "string"
  description = "The title of the message that will be sent by the notification service"
}
