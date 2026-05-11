# Workforce (`product/workforce`)

Employees, contracts, and organisational structure.

## Responsibilities

- Employee profiles (personal data, status, department)
- Contract management (type, hours per week, effective dates)
- Organisational hierarchy

## Key design decisions

Contract type drives the cost-rule engine in `product/costing` — the contract attached to an employee determines which overtime and holiday rules apply.

Employee status (active / inactive) gates access to other modules: only active employees can submit time reports.
