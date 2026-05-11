# Approvals (`product/approvals`)

Multi-step approval workflow with full status history.

## Responsibilities

- Define approval chains per tenant (who approves what, in what order)
- Track each step's decision (approve / reject) with timestamp and actor
- Notify the submitter on final decision
- Expose inbox views for approvers (pending / approved / rejected)

## Key design decisions

Every state transition is recorded as an immutable history entry. The current status is derived from the latest entry — there is no mutable status field on the approval record itself. This gives a full audit trail with no extra effort.

An approval chain can have multiple sequential steps. All steps must be approved before the time report moves to `APPROVED`. A rejection at any step short-circuits the chain.

## States

```
PENDING → APPROVED (all steps passed)
        → REJECTED (any step rejected)
```
