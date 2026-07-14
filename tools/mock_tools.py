"""
Checks the status of enterprise services.
"""

# Mock data
MOCK_SERVICES = {
    "nginx": {"status": "down", "cpu_percent": 12, "last_restart": "3 days ago"},
    "database": {"status": "healthy", "cpu_percent": 34, "last_restart": "14 days ago"},
    "auth-service": {"status": "degraded", "cpu_percent": 91, "last_restart": "1 hour ago"},
    "payment-gateway": {"status": "healthy", "cpu_percent": 22, "last_restart": "7 days ago"}
}

def check_service_status(service_name: str) -> dict:
    service_name = service_name.lower().strip()
    if service_name not in MOCK_SERVICES:
        return {"error": f"Unknown service '{service_name}'. Known services: {list(MOCK_SERVICES.keys())}"}
    return {"service": service_name, **MOCK_SERVICES[service_name]}