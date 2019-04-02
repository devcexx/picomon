import os
import json
import boto3
from io import BytesIO
from enum import Enum
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from botocore.exceptions import ClientError
import traceback
import time
import socket
from common import *

# This variable is (and MUST) be the only global mutable variable.
# Contains the state of the previous execution of the current function.
# It is used as a state cache to reduce the accesses to AWS S3, when the
# function was already "warmed-up".

# A value of None indicates that the AWS Lambda container has just been
# "cold-started" and a S3 access will be required.
CURRENT_STATE = None

class State:
    def __init__(self, service_state=ServiceState.HEALTHY, attempts=0):
        self.service_state = service_state
        self.attempts = attempts
        self.commit()

    def _get_state_dict(self):
        state = self.__dict__.copy()
        state.pop("_org_state", None)
        return state

    def serialize(self):
        return json.dumps(self._get_state_dict())

    def is_dirty(self):
        return self._org_state != self._get_state_dict()

    def commit(self):
        self._org_state = self._get_state_dict()

    @staticmethod
    def deserialize(data):
        return State(**json.loads(data))

    def __str__(self):
        return f"State{self._get_state_dict()}"

def load_state(bucket, key):
    data = BytesIO()
    try:
        bucket.download_fileobj(key, data)
        state = State.deserialize(data.getvalue().decode('utf-8'))
    except ClientError as ex:
        if ex.response['Error']['Code'] == '404':
            print(f"State file not found: {bucket.name}/{key}. Setting to default")
            state = State()
            
            # Force saving if it does not exist
            save_state(state, bucket, key)
        else:
            raise ex
    except Exception as ex:
        print(f"Couldn't restore state from {bucket.name}/{key}. Setting to default")
        state = State()
        traceback.print_exc()

    return state

def save_state(state, bucket, key):
    data = state.serialize().encode('utf-8')
    bucket.put_object(Key=key, Body=data)

def check_health(url, timeout):
    try:
        req = Request(url)
        req.add_header("User-Agent", "acm-monitor/1.0")
        req.method = "HEAD"

        with urlopen(req, timeout=timeout) as res:
            res.read()

        return {
            "result": HealthCheckResult.OK
        }
    except HTTPError as ex:
        return {
            "result": HealthCheckResult.HTTP_ERROR,
            "http_status": ex.code
        }
    except URLError as ex:
        if isinstance(ex.reason, socket.timeout):
            return {
                "result": HealthCheckResult.TIMEOUT
            }

        return {
            "result": HealthCheckResult.UNKNOWN_ERROR,
            "exception": ex
        }

    except Exception as ex:
        return {
            "result": HealthCheckResult.UNKNOWN_ERROR,
            "exception": ex
        }

def take_service_name(url):
    url_components = urlparse(url)
    scheme = url_components.scheme

    if scheme not in ['https', 'http']:
        raise RuntimeError(f"Unsupported URL Scheme: {scheme}")

    netloc = url_components.netloc
    colon_idx = netloc.rfind(":")
    if colon_idx == -1:
        host = netloc
        if scheme == "https":
            port = 443
        else:
            port = 80
    else:
        host = netloc[:colon_idx]
        port = netloc[(colon_idx+1):]

    return f"{url_components.scheme}-{host}-{port}"

def handle_call(event, context):
    global CURRENT_STATE

    print("Preparing health check!")

    target_url = env_or_failure("MON_TARGET_URL")
    cloudwatch_namespace = env_or_default("MON_CWATCH_NAMESPACE", None)
    cloudwatch_latency_metric_name = env_or_default("MON_CWATCH_METRIC_LATENCY", None)
    cloudwatch_state_metric_name = env_or_default("MON_CWATCH_METRIC_STATE", None)
    cloudwatch_http_status_metric_name = env_or_default("MON_CWATCH_METRIC_HTTP_STATUS", None)
    receiver_topic_arn = env_or_failure("MON_RECEIVER_ARN")
    state_bucket_name = env_or_failure("MON_STATE_BUCKET")
    http_timeout = int(env_or_default("MON_REQUEST_TIMEOUT", "10"))
    
    s3_state_key = f"{context.function_name}-{context.function_version}-{take_service_name(target_url)}.json"
    s3 = boto3.resource('s3')
    state_bucket = s3.Bucket(state_bucket_name)

    if CURRENT_STATE is None:
        print("Will load state from S3")
        state = load_state(state_bucket, s3_state_key)
        CURRENT_STATE = state
    else:
        state = CURRENT_STATE
        print("State is cached on memory. Using it")

    print(f"Current state: {state}")

    print(f"Requesting {target_url}...")
    beg_time = time.time()
    res = check_health(target_url, http_timeout)
    elapsed = (time.time() - beg_time) * 1000
    result = res["result"]

    if result == HealthCheckResult.OK:
        service_state = ServiceState.HEALTHY
    else:
        service_state = ServiceState.UNHEALTHY

    if result == HealthCheckResult.OK:
        status_message = "Request OK. Took: %d ms" % elapsed
    elif result == HealthCheckResult.TIMEOUT:
        status_message = "Request timed-out"
    elif result == HealthCheckResult.HTTP_ERROR:
        status_message = "Request returned HTTP status %d in %d ms" % (res["http_status"], elapsed)
    else:
        ex = res["exception"]
        ex_str = str(ex)
        status_message = f"Request failure: {ex_str}"

        # Change the exception stored in the result with a descriptive string, so
        # it can be serialized to be returned as a result of the execution.
        res["exception"] = ex_str

    print(f"Result: {status_message}")

    if service_state == state.service_state:
        # If the state did not change, just keep the number of attempts in zero
        state.attempts = 0
    else:
        # If the got service state is different from the saved one, we add one
        # to the attempt counter, If the attempt count reaches a specific number,
        # the service state will switch to the just obtained one.
        state.attempts += 1


    if state.attempts >= 3: # Hardcored value from now
        # The monitor has returned a state for the service, different to the one
        # saved in the current state, for a reasonable number of attempts. Here
        # the service state must be updated, and the number of attempts resetted.
        state.service_state = service_state
        state.attempts = 0

        # Now we have to notify the SNS topic about this change.
        str_message = f"The endpoint {target_url} has changed its state to {ServiceState.name(service_state)}."

        if service_state == ServiceState.UNHEALTHY:
            str_message += f"\nThe last request result was: {status_message}"

        sns_json_body = {
            "default": str_message,
            "lambda": json.dumps({
                "endpoint": target_url,
                "new_state": service_state,
                "last_health_check_result_desc": status_message,
                "last_health_check_result": res
            })
        }

        boto3.client('sns').publish(
            TargetArn=receiver_topic_arn,
            Subject=f"Endpoint {target_url} status changed to {ServiceState.name(service_state)}",
            Message=json.dumps(sns_json_body),
            MessageStructure="json")

    if cloudwatch_namespace != "" and cloudwatch_namespace is not None:
        cwatch = boto3.client('cloudwatch')

        print("Publishing metrics")
        metric_dimensions = [
            {
                "Name": "MonitorName",
                "Value": context.function_name
            }
        ]

        metrics_data = []
        if cloudwatch_latency_metric_name != "" and cloudwatch_latency_metric_name is not None and \
           result in [HealthCheckResult.OK, HealthCheckResult.HTTP_ERROR]:
            # Only published if enabled and the request has been executed correctly
            metrics_data.append({
                "MetricName": cloudwatch_latency_metric_name,
                "Dimensions": metric_dimensions,
                'Value': elapsed,
                'Unit': 'Milliseconds',
                'StorageResolution': 60
            })

        if cloudwatch_state_metric_name != "" and cloudwatch_state_metric_name is not None:
            metrics_data.append({
                "MetricName": cloudwatch_state_metric_name,
                "Dimensions": metric_dimensions,
                # Take the effective service state NOT the just computed one. (state.service_state != service_state)
                'Value': state.service_state,
                'Unit': 'None',
                'StorageResolution': 60
            })

        if cloudwatch_http_status_metric_name != "" and cloudwatch_http_status_metric_name is not None:
            if result == HealthCheckResult.OK:
                publishing_state = 200
            else:
                publishing_state = res.get("http_status")

            if publishing_state is not None:
                metrics_data.append({
                    "MetricName": cloudwatch_http_status_metric_name,
                    "Dimensions": metric_dimensions,
                    'Value': publishing_state,
                    'Unit': 'None',
                    'StorageResolution': 60
                })

        if len(metrics_data) > 0:
            cwatch.put_metric_data(Namespace=cloudwatch_namespace,
                                   MetricData=metrics_data)

    print(f"New state: {state}")
    if state.is_dirty():
        print("State altered. Will be saved")
        save_state(state, state_bucket, s3_state_key)
        state.commit()
    else:
        print("State unaltered. Won't be saved")

    return json.dumps({
        "health_check_result": res,
        "final_state": state.serialize()
    })

# For testing xd
class TestContext:
    def __init__(self, function_name, function_version):
        self.function_name = function_name
        self.function_version = function_version
