# Request Workflows

### I. Leave Request

```text
Employee submits leave request
        ↓
Agent identifies Leave Request
        ↓
Retrieve relevant Leave Policy
        ↓
Get Employee Profile
        ↓
Get Leave Balance
        ↓
Validate request
        ↓
Apply deterministic eligibility rules
        ↓
Generate recommendation
        ↓
Submit to HR
        ↓
HR Approves / Rejects
        ↓
Update request status
        ↓
Audit Log
```

### II. Expense/Reimbursment Claim

```text
Employee submits expense claim
        ↓
Agent identifies Expense Claim
        ↓
Retrieve Expense Policy
        ↓
Get Employee Profile
        ↓
Validate claim information
        ↓
Check expense category
        ↓
Apply reimbursement rules
        ↓
Calculate eligible amount
        ↓
Generate recommendation
        ↓
Submit to HR / Finance
        ↓
Approve / Reject
        ↓
Update request
        ↓
Audit Log
```

### III. Health / Benefits Claim

```text
Employee submits health/benefits claim
        ↓
Agent identifies Benefits Claim
        ↓
Retrieve relevant Benefits Policy
        ↓
Get Employee Benefits Profile
        ↓
Validate claim information
        ↓
Check benefit eligibility
        ↓
Calculate eligible coverage
        ↓
Generate recommendation
        ↓
Submit to HR
        ↓
HR Approves / Rejects
        ↓
Update request
        ↓
Audit Log
```
