# Agent Responsbilities and Decision Flow

### I. Agent Responsibilites

#### A. What The Agent Does

1. Understand the User
2. Decide Which Tools Are Required
3. Retrive Policy Knowledge
4. Gather Business Information
5. Invoke Deterministics Business Logic
6. Explain the Result
7. Manage The Workflow

#### B. What The Agent Must Not Do

1. Determine Eligibility
2. Calculate Reimbursement
3. Calculate Leave Balance
4. Approve Request

### II. Agent Decision Flow

```text
                         Employee
                            │
                            ▼
                     Natural Language
                            │
                            ▼
                    ┌───────────────┐
                    │  HR AI Agent  │
                    └───────┬───────┘
                            │
                 Classify Request
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
         LEAVE           EXPENSE         BENEFITS
            │               │               │
            └───────────────┼───────────────┘
                            │
                    Retrieve HR Policy
                            │
                            ▼
                       RAG / pgvector
                            │
                            ▼
                    Retrieve Employee Data
                            │
                            ▼
                    Deterministic Rules
                            │
                            ▼
                     Structured Result
                            │
                            ▼
                  Agent Recommendation
                            │
                            ▼
                    HR Review Dashboard
                       │           │
                   APPROVE       REJECT
                       │           │
                       └─────┬─────┘
                             ▼
                        Audit Trail
```
