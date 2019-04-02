# Picomon
Simple, serverless, low-cost service monitor deployable on Amazon Web
Services, that allows you to monitorize the status of any HTTP/S
endpoints and receive notification updates through Telegram.

## Prerequisites

* Python3 with `pip` installed.
* Terraform, for deploying the infrastructure.

## Components

Once deployed, the monitor will be composed by the following AWS resources:

* A SNS Topic, that will receive the state updates and broadcast them
  among all its subscriptors. By default, it will only send
  notifications to Telegram, but you might create your own
  subscriptions (email, SMS, etc)
* A Lambda function, that will receive the updates from SNS, and
  forward it to the recipients specified in the config.
* Some lambda functions, one per monitorized service, that will be in
  charge of periodically make requests to the services to check their
  status.
* Some Cloudwatch events, one per monitorized service, that will
  execute each Lambda monitor of each service one time each minute, to
  perform the checks.
* A S3 bucket, that will store the state of all the
  monitors. Everytime a monitorized service changes its status, it is
  saved on the bucket. Usually, the monitor will grab its own state
  from a cache on the Lambda function itself, but it might fully
  reload its state from the bucket if a "cold-start" occurs.
* All the required IAM roles & policies.

## Deployment

1. Copy the `deploy-config.sh.template` file to `deploy-config.sh`
2. Modify the `deploy-config.sh` to change the monitor configuration
   fit your needs (More info on the file itself)
3. Run `make deploy`. This will deploy all your configured monitors to
   your AWS account.
   
## Pricing

The best way to use this monitor is to take advantage of the AWS Free
Tier, that will make you to be able to run up to (theorically) 13
different monitors with a near-free price.

If don't, you'll probably be charged with about $0.40/service, mainly
for the executions of the Lambda functions that monitorize the services.

Also, if you enable the upload of CloudWatch metrics and you are out
of the AWS Free Tier, you'll be charged for each custom metric
measured by each monitor. You can fully disable CloudWatch metrics
from the monitors, anyway.

## License

This software is distributed under the GNU GPL License v3.0. You can
freely use this software, and modify it. But if you distribute some
modification, do it for everyone!.
