.PHONY: verify-e2e verify-e2e-verbose report-order report-order-full report-last-order verify-report

# Run automated end-to-end verification (mint token -> seed analyst -> ingest -> list jobs)
verify-e2e:
	bash scripts/verify_e2e.sh

# Same as verify-e2e but with verbose curl (-v) output for debugging
verify-e2e-verbose:
	CURL_VERBOSE=1 bash -x scripts/verify_e2e.sh

# Report by OrderId (requires ORDER_ID env var)
report-order:
	@if [ -z "$$ORDER_ID" ]; then echo "ORDER_ID is required, e.g.: make report-order ORDER_ID=68abcdef..."; exit 2; fi
	bash scripts/report_by_order.sh

# Full JSON (pipe to jq yourself for extra fields)
report-order-full:
	@if [ -z "$$ORDER_ID" ]; then echo "ORDER_ID is required, e.g.: make report-order-full ORDER_ID=68abcdef..."; exit 2; fi
	GATEWAY_BASE=$${GATEWAY_BASE:-http://localhost:8000} \
	SCHED_BASE=$${SCHED_BASE:-http://localhost:8004} \
	FULL=1 bash scripts/report_by_order.sh

# Convenience: Report using last ORDER_ID persisted by verify_e2e.sh
report-last-order:
	@if [ ! -f scripts/.last_order_id ]; then echo "No saved ORDER_ID found. Run 'make verify-e2e' first or use 'make report-order ORDER_ID=...'"; exit 2; fi
	ORDER_ID=$$(cat scripts/.last_order_id) bash scripts/report_by_order.sh

# Alias for clarity
verify-report: report-order
