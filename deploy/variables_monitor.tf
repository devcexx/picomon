variable "monitors" {
  type = "map"
  description = "A map that defines the monitors that will be deployed. The keys of the map are the names of each monitor and each value, the endpoint that will be monitored"
}

variable "monitor_execution_timeout" {
  type = "string"
  description = "The monitors' execution timeout, in seconds"
}

variable "cwatch_namespace" {
  type = "string"
  description = "The custom metrics namespace where the monitors will place their metrics. An empty value means that metrics will be disabled"
  default = ""
}

variable "cwatch_latency_metric_name" {
  type = "string"
  description = "The name of the custom metric that shows the latency changes of the monitorized server in over the time. An empty value means that this metric will be disabled."
  default = ""
}

variable "cwatch_state_metric_name" {
  type = "string"
  description = "The name of the custom metric that shows the service status changes over the time. An empty value means that this metric will be disabled."
  default = ""
}

variable "cwatch_http_status_metric_name" {
  type = "string"
  description = "The name of the custom metric that shows the different HTTP status returned by the monitorized service over the time. An empty value means that this metric will be disabled."
  default = ""
}

variable "http_request_timeout" {
  type = "string"
  description = "The max timeout for the requests performed against the monitorized services"
  default = "10"
}

variable "monitor_function_package" {
  type = "string"
  description = "The path of the zip file that contains a prepared distribution for the monitor function"
}
