# Business Rules

### I. Leave Request

#### A. Employment Eligibility

```text
Employee Status = ACTIVE
```

#### B. Leave Balance

```text
Requested Days ≤ Available Leave Balance
```

#### C. Maximum Consecutive Days

```text
Requested Days ≤ Policy Maximum
```

#### D. Advanced Notice

```text
Request Date + Minimum Notice Period ≤ Leave Start Date
```

#### E. Overlapping Leave

```text
New Leave Period
    MUST NOT overlap
Existing Approved Leave
```

### II. Expense/Reimbursment Claim

#### A. Employee Eligibility

```text
Employee Status = ACTIVE
```

#### B. Supported Category

```text
Expense Category ∈ Allowed Categories
```

#### C. Maximum Claim

```text
Claim Amount ≤ Category Limit
```

#### D. Reimbursement Percentage

```text
Eligible Amount =
    Claim Amount × Reimbursement Rate
```

#### E. Duplicate Claim

```text
Same Employee
+ Same Expense Date
+ Same Amount
+ Same Category
→ Possible Duplicate
```

#### F. Required Documentation

```text
Required Receipt = TRUE
→ Receipt Must Exist
```

### III. Health / Benefits Claim

#### A. Employee Eligibility

#### B. Benefit Eligibility

```text
Employee Benefit Plan
    MUST include requested benefit
```

#### C. Coverage Percentage

```text
Eligible Amount =
    Claim Amount × Coverage Percentage
```

#### D. Annual Limit

```text
Eligible Amount
    ≤ Remaining Annual Benefit Limit
```

#### E. Waiting Period

```text
Employee Benefit Start Date
    + Waiting Period
    ≤ Claim Date
```

#### F. Required Documentation

```text
Required Medical Document
    MUST exist
```
