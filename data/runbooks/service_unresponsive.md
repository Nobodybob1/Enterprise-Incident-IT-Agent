# Runbook: Service Unresponsive

## Symptoms
- Health check endpoint returns timeout or 5xx errors
- Users report the application is "hanging" or not loading
- No new log entries being written

## Diagnosis Steps
1. Check process status: `systemctl status <service-name>`
2. Check CPU/memory usage: `top` or `htop`
3. Check recent error logs: `journalctl -u <service-name> -n 100`

## Resolution
1. Attempt a graceful restart: `systemctl restart <service-name>`
2. If restart fails, check for port conflicts: `lsof -i :<port>`
3. If memory usage is at capacity, check for memory leaks in recent deploys
4. **Always require human approval before restarting a production service**

## Escalation
If the service fails to recover after two restart attempts, escalate to
on-call engineering and consider rolling back the most recent deployment.
