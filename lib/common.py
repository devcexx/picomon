import os
class ServiceState:
    HEALTHY = 1
    UNHEALTHY = 2

    def name(state):
        if state == ServiceState.HEALTHY:
            return "HEALTHY"
        elif state == ServiceState.UNHEALTHY:
            return "UNHEALTHY"
        else:
            return "UNKNOWN"

class HealthCheckResult:
    OK = 1
    TIMEOUT = 2
    HTTP_ERROR = 3
    UNKNOWN_ERROR = 4

    
def env_or_default(key, default):
    value = os.environ.get(key)
    if value is None:
        return default
    else:
        return value

def env_or_failure(key):
    value = os.environ.get(key)
    if value is None:
        raise RuntimeError(f"Undefined required environment variable '{key}'")
    return value
