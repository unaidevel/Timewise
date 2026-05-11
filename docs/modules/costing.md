# Costing (`product/costing`)

Configurable rule engine that maps logged hours to labour costs.

## Responsibilities

- Define cost rules per contract type (base rate, overtime multipliers, holiday rates)
- Apply rules to an approved time report to produce a cost breakdown
- Store cost results for reporting

## Key design decisions

Rules are data-driven, not hardcoded. A new contract type or overtime policy is added by inserting a rule record, not by changing application code.

Cost calculation runs against approved reports only — pending or rejected reports produce no cost output. This makes the cost ledger auditable and consistent with the approval state.
