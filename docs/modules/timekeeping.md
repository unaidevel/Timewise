# Timekeeping (`product/timekeeping`)

Time reports, shift entries, overtime detection, and the submission flow.

## Responsibilities

- Time report creation and management per period
- Individual shift entry logging (time in / time out)
- Automatic overtime detection based on contract rules
- Submission for approval

## Key design decisions

A **time report** groups all shift entries for a given employee and period. It is the unit submitted for approval — not individual entries.

Overtime is computed at submission time by comparing total logged hours against the contracted weekly hours. The result is stored on the report so recalculation does not depend on the contract state at review time.

## States

```
DRAFT → SUBMITTED → APPROVED
                 └→ REJECTED → SUBMITTED (resubmission)
```
