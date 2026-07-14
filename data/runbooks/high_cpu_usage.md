# Runbook: High CPU Usage

## Symptoms
- Server monitoring alerts CPU usage above 90% sustained for 5+ minutes
- Application response times increasing
- Possible request queueing or timeouts

## Diagnosis Steps
1. Identify top CPU-consuming processes: `top -o %CPU`
2. Check if usage correlates with a recent deploy or traffic spike
3. Review autoscaling group status if applicable

## Resolution
1. If a single runaway process is identified, restart it (with approval)
2. If traffic-driven, scale out additional instances
3. If caused by a recent deploy, consider rollback
4. Monitor for 15 minutes post-fix to confirm resolution

## Escalation
Sustained high CPU after scaling and restart should be escalated to the
platform engineering team to investigate a potential code-level issue.
