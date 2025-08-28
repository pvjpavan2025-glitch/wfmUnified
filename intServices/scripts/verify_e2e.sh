#!/usr/bin/env bash
set -euo pipefail

# Automated end-to-end verification:
# - Mint dev JWT via API Gateway
# - Health checks (intServices, rules, scheduler)
# - Seed an analyst if none exists for the tenant
# - Ingest OSM order via intServices with orchestrate/split/auto_schedule
# - List jobs (and optionally schedule a pending one)

# Resolve script dir to allow relative paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Configurable endpoints and settings (override via env)
INT_BASE="${INT_BASE:-http://localhost:8082}"
GATEWAY_BASE="${GATEWAY_BASE:-http://localhost:8000}"
RULES_BASE="${RULES_BASE:-http://localhost:8003}"
SCHED_BASE="${SCHED_BASE:-http://localhost:8004}"
ORDER_BASE="${ORDER_BASE:-http://localhost:8008}"

API_KEY_NAME="${API_KEY_NAME:-X-API-Key}"
API_KEY="${API_KEY:-change-me-please}"

TENANT_ID="${TENANT_ID:-dev-tenant}"
USER_ID="${USER_ID:-dev-user}"
USERNAME="${USERNAME:-dev}"
ROLES_JSON="${ROLES_JSON:-[\"admin\"]}"
EXPIRES_MIN="${EXPIRES_MIN:-60}"

# Path to sample input JSON; default assumes repo layout: ../references relative to intServices/
INPUT_JSON="${INPUT_JSON:-$SCRIPT_DIR/../../references/input-order.json}"

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[1;33m'
NC='\033[0m'

echo -e "${YEL}==> Verifying prerequisites...${NC}"
if ! command -v jq >/dev/null 2>&1; then
  echo -e "${RED}jq is required but not installed. On macOS: brew install jq${NC}"
  exit 1
fi

if [ ! -f "$INPUT_JSON" ]; then
  echo -e "${RED}Input JSON not found at: $INPUT_JSON${NC}"
  echo "Set INPUT_JSON=/absolute/path/to/input.json to override"
  exit 1
fi

echo -e "${YEL}==> Minting dev JWT via API Gateway (${GATEWAY_BASE})...${NC}"

# Allow external token via WFM_JWT env var; otherwise mint one
if [ -n "${WFM_JWT:-}" ]; then
  ACCESS_TOKEN="$WFM_JWT"
  echo -e "${GRN}Using JWT from WFM_JWT environment variable${NC}"
else
  TOKEN_RESP=$(curl -s -S -X POST "$GATEWAY_BASE/auth/token/test" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$USER_ID\",\"username\":\"$USERNAME\",\"tenant_id\":\"$TENANT_ID\",\"roles\":$ROLES_JSON,\"expires_in_minutes\":$EXPIRES_MIN}")
  if [ -z "$TOKEN_RESP" ] || [ "$(echo "$TOKEN_RESP" | jq -r 'has("access_token")')" != "true" ]; then
    echo -e "${RED}Failed to mint token. Response:${NC}"
    echo "$TOKEN_RESP"
    exit 1
  fi
  ACCESS_TOKEN=$(echo "$TOKEN_RESP" | jq -r .access_token)
fi

echo -e "${GRN}Token acquired for tenant ${TENANT_ID}${NC}"

echo -e "\n${YEL}==> Health checks${NC}"
curl -s "$INT_BASE/healthz" -H "$API_KEY_NAME: $API_KEY" | jq . || true
curl -s "$RULES_BASE/health" | jq . || true
curl -s "$SCHED_BASE/health" -H "Authorization: Bearer $ACCESS_TOKEN" | jq . || true

echo -e "\n${YEL}==> Ensure an active analyst exists for tenant ${TENANT_ID}${NC}"
AN_COUNT=$(curl -s "$SCHED_BASE/analysts?skip=0&limit=1" -H "Authorization: Bearer $ACCESS_TOKEN" | jq 'length')
if [ "${AN_COUNT}" = "0" ]; then
  echo "No analysts found. Seeding a default analyst..."
  SEED_RESP=$(curl -s -S -X POST "$SCHED_BASE/analysts" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\n      \"name\": \"Auto Analyst\",\n      \"email\": \"auto-analyst@example.com\",\n      \"tenant_id\": \"$TENANT_ID\",\n      \"skills\": [\"fiber\", \"splicing\"],\n      \"experience_years\": 3,\n      \"max_concurrent_jobs\": 3,\n      \"availability\": {\"mon\": [\"09:00-17:00\"]},\n      \"status\": \"active\"\n    }")
  echo "$SEED_RESP" | jq . || true
else
  echo "Analyst exists (${AN_COUNT})."
fi

echo -e "\n${YEL}==> Ingest OSM order via intServices with orchestrate+split+auto_schedule${NC}"
INGEST_RESP=$(curl -s -S -X POST "$INT_BASE/ingest/osm?orchestrate=true&split_jobs=true&auto_schedule=true" \
  -H "$API_KEY_NAME: $API_KEY" \
  -H 'Content-Type: application/json' \
  --data-binary @"$INPUT_JSON")
# Show a compact meaningful summary if possible
if echo "$INGEST_RESP" | jq empty 2>/dev/null; then
  echo "$INGEST_RESP" | jq '{status: (.status // "ok"), jobs: (.rules_response?.jobs? // .jobs? // [] | length), schedules: (.rules_response?.schedules? // .schedules? // [] | length)}'
else
  echo "$INGEST_RESP"
fi

# Extract created order_id if present for reporting
ORDER_ID=$(echo "$INGEST_RESP" | jq -r '.order._id // .order.id // .canonical.order_id // empty') || ORDER_ID=""
if [ -n "$ORDER_ID" ] && [ "$ORDER_ID" != "null" ]; then
  echo -e "\n${YEL}==> Report: Jobs summary by order ${ORDER_ID}${NC}"
  REPORT=$(curl -s -S "$SCHED_BASE/reports/orders/$ORDER_ID/jobs-summary" -H "Authorization: Bearer $ACCESS_TOKEN")
  echo "$REPORT" | jq '{order_id, total_jobs, status_counts, assignment}' || echo "$REPORT"
  # Persist last ORDER_ID for convenience
  echo -n "$ORDER_ID" > "$SCRIPT_DIR/.last_order_id"
  echo -e "Saved last ORDER_ID to $SCRIPT_DIR/.last_order_id"
else
  echo -e "\n${YEL}==> No order_id in ingest response; creating a READY order directly and validating report${NC}"
  EXT_ID="OSM-VERIF-$(date +%s)"
  NEW_ORDER=$(curl -s -S -X POST "$GATEWAY_BASE/auth/token/test" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$USER_ID\",\"username\":\"$USERNAME\",\"tenant_id\":\"$TENANT_ID\",\"roles\":$ROLES_JSON,\"expires_in_minutes\":$EXPIRES_MIN}")
  ACCESS_FALLBACK=$(echo "$NEW_ORDER" | jq -r .access_token)
  CREATED=$(curl -s -S -X POST "$ORDER_BASE/orders" \
    -H "Authorization: Bearer $ACCESS_FALLBACK" \
    -H 'Content-Type: application/json' \
    -d "{\"external_id\":\"$EXT_ID\",\"source\":\"OSM\",\"payload\":{\"externalId\":\"$EXT_ID\",\"serviceOrderItems\":[{\"id\":\"item-1\"}]},\"status\":\"ready\"}")
  ORDER_ID=$(echo "$CREATED" | jq -r '._id // .id // empty')
  if [ -n "$ORDER_ID" ]; then
    curl -s -S -X POST "$RULES_BASE/orders/process-ready" -H "Authorization: Bearer $ACCESS_FALLBACK" >/dev/null || true
    echo -e "${YEL}==> Report: Jobs summary by order ${ORDER_ID}${NC}"
    REPORT=$(curl -s -S "$SCHED_BASE/reports/orders/$ORDER_ID/jobs-summary" -H "Authorization: Bearer $ACCESS_FALLBACK")
    echo "$REPORT" | jq '{order_id, total_jobs, status_counts, assignment}' || echo "$REPORT"
    # Persist last ORDER_ID for convenience
    echo -n "$ORDER_ID" > "$SCRIPT_DIR/.last_order_id"
    echo -e "Saved last ORDER_ID to $SCRIPT_DIR/.last_order_id"
  fi
fi

echo -e "\n${YEL}==> List jobs (tenant-scoped)${NC}"
JOBS=$(curl -s -S "$SCHED_BASE/jobs?skip=0&limit=5" -H "Authorization: Bearer $ACCESS_TOKEN")

# If response is not an array (likely auth error), try one retry with a freshly minted token
if ! echo "$JOBS" | jq -e 'type == "array"' >/dev/null 2>&1; then
  echo -e "${YEL}Jobs endpoint did not return an array (auth or other error). Attempting a fresh token and retry...${NC}"
  RETOKEN=$(curl -s -S -X POST "$GATEWAY_BASE/auth/token/test" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":\"$USER_ID\",\"username\":\"$USERNAME\",\"tenant_id\":\"$TENANT_ID\",\"roles\":$ROLES_JSON,\"expires_in_minutes\":$EXPIRES_MIN}")
  ACCESS_TOKEN=$(echo "$RETOKEN" | jq -r .access_token)
  JOBS=$(curl -s -S "$SCHED_BASE/jobs?skip=0&limit=5" -H "Authorization: Bearer $ACCESS_TOKEN")
fi

if echo "$JOBS" | jq -e 'type == "array"' >/dev/null 2>&1; then
  COUNT=$(echo "$JOBS" | jq 'length')
  echo "$JOBS" | jq '[.[] | {id: (._id // .id), name: .name, status: .status, assigned_analyst: .assigned_analyst}]'
  if [ "$COUNT" = "0" ]; then
    echo -e "${RED}No jobs found. Check tenant consistency and earlier responses.${NC}"
    exit 2
  fi
else
  echo -e "${RED}Jobs API response is not an array. Raw response below:${NC}"
  echo "$JOBS" | jq . || echo "$JOBS"
  exit 5
fi

# Optionally schedule the first pending job
FIRST_STATUS=$(echo "$JOBS" | jq -r '.[0].status // ""')
FIRST_ID=$(echo "$JOBS" | jq -r '.[0]._id // empty')
if [ "$FIRST_STATUS" = "pending" ] && [ -n "$FIRST_ID" ]; then
  echo -e "\n${YEL}==> Scheduling first pending job: $FIRST_ID${NC}"
  SCHED_RESP=$(curl -s -S -X POST "$SCHED_BASE/jobs/$FIRST_ID/schedule" -H "Authorization: Bearer $ACCESS_TOKEN")
  echo "$SCHED_RESP" | jq . || echo "$SCHED_RESP"
fi

echo -e "\n${GRN}E2E verification complete.${NC}"
