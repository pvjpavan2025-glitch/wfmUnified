#!/usr/bin/env bash
set -euo pipefail

# Report jobs summary for a given ORDER_ID using Scheduler Service.
# Usage:
#   ORDER_ID=<mongo_id> ./scripts/report_by_order.sh
# Optional env:
#   GATEWAY_BASE (default http://localhost:8000) used to mint a JWT if WFM_JWT not given
#   SCHED_BASE   (default http://localhost:8004)
#   TENANT_ID    (default dev-tenant)
#   USER_ID, USERNAME, ROLES_JSON, EXPIRES_MIN

ORDER_ID="${ORDER_ID:-}"
if [ -z "$ORDER_ID" ]; then
  echo "ORDER_ID is required. Usage: ORDER_ID=<mongo_id> $0" >&2
  exit 2
fi

GATEWAY_BASE="${GATEWAY_BASE:-http://localhost:8000}"
SCHED_BASE="${SCHED_BASE:-http://localhost:8004}"
TENANT_ID="${TENANT_ID:-dev-tenant}"
USER_ID="${USER_ID:-dev-user}"
USERNAME="${USERNAME:-dev}"
ROLES_JSON="${ROLES_JSON:-[\"admin\"]}"
EXPIRES_MIN="${EXPIRES_MIN:-60}"

# Helper to mint a fresh token
mint_token() {
  curl -s -S -X POST "$GATEWAY_BASE/auth/token/test" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$USER_ID\",\"username\":\"$USERNAME\",\"tenant_id\":\"$TENANT_ID\",\"roles\":$ROLES_JSON,\"expires_in_minutes\":$EXPIRES_MIN}" | jq -r .access_token
}

# Choose initial token: use WFM_JWT if set; otherwise mint
ACCESS_TOKEN="${WFM_JWT:-}"
if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
  ACCESS_TOKEN="$(mint_token)"
fi

request_report() {
  curl -s -S "$SCHED_BASE/reports/orders/$ORDER_ID/jobs-summary" \
    -H "Authorization: Bearer $1"
}

REPORT=$(request_report "$ACCESS_TOKEN")

# If response indicates auth error or lacks expected fields, retry once with a fresh token
NEED_RETRY="false"
if echo "$REPORT" | jq -e 'type=="object" and (has("detail") or (has("order_id")|not))' >/dev/null 2>&1; then
  NEED_RETRY="true"
fi

if [ "$NEED_RETRY" = "true" ]; then
  FRESH_TOKEN="$(mint_token)"
  if [ -n "$FRESH_TOKEN" ] && [ "$FRESH_TOKEN" != "null" ]; then
    REPORT=$(request_report "$FRESH_TOKEN")
  fi
fi

# Output: summary (default) or full when FULL=1
if echo "$REPORT" | jq empty 2>/dev/null; then
  if [ "${FULL:-0}" = "1" ]; then
    echo "$REPORT" | jq .
  else
    # If the API returned an empty object, note it to avoid confusing nulls
    if echo "$REPORT" | jq -e 'type=="object" and length==0' >/dev/null 2>&1; then
      echo "{}" | jq '{order_id: null, total_jobs: 0, status_counts: {}, assignment: {assigned: 0, unassigned: 0}}'
    else
      echo "$REPORT" | jq '{order_id, total_jobs, status_counts, assignment}'
    fi
  fi
else
  echo "$REPORT"
fi
