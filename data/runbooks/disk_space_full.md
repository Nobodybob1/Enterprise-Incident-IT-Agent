# Runbook: Disk Space Full

## Symptoms
- Application logs show "No space left on device"
- Server monitoring shows disk usage above 95%
- New file writes fail; services may crash on write attempts

## Diagnosis Steps
1. Check disk usage: `df -h`
2. Identify largest directories: `du -sh /var/log/* | sort -rh | head -10`
3. Check for oversized log files or core dumps

## Resolution
1. Rotate and compress old logs: `logrotate -f /etc/logrotate.conf`
2. Delete files older than 30 days in `/var/log/archive`
3. Clear temp directory: `rm -rf /tmp/*` (only if safe — confirm no active jobs)
4. If disk is still full, resize the volume or archive data to cold storage

## Escalation
If disk fills again within 24 hours, escalate to Infrastructure team —
likely a runaway process or log misconfiguration.
