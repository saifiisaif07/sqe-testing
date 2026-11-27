# Part A — Black-Box Testing Report

**System under test:** Student Course Registration System  
**Source of expected behavior:** `REQUIREMENTS.md`, FR-01 through FR-15  
**Test implementation:** `tests/test_blackbox.py`

## A1. Equivalence Class Partitioning (ECP)

| Requirement | Input dimension / class | Representative input | Expected output | Test ID |
|---|---|---|---|---|
| FR-04, FR-09 | Dues — valid, zero | dues = Rs. 0 | `REGISTERED` | ECP-01 |
| FR-04, FR-09 | Dues — valid, positive | dues = Rs. 1 | `DUES_BLOCK` | ECP-02 |
| FR-15 | Dues — invalid, negative | dues = Rs. -1 | `ValueError("Invalid dues")` | ECP-03 |
| FR-03 | Prerequisites — valid, none required | required = ∅ | `REGISTERED` | ECP-04 |
| FR-03, FR-06 | Prerequisites — valid, all completed | required = {CS101, MATH101}; completed = both | `REGISTERED` | ECP-05 |
| FR-03, FR-06 | Prerequisites — invalid, only some completed | required = {CS101, MATH101}; completed = {CS101} | `PREREQUISITES_MISSING` | ECP-06 |
| FR-03, FR-06 | Prerequisites — invalid, none completed | required = {CS101}; completed = ∅ | `PREREQUISITES_MISSING` | ECP-07 |
| FR-08 | Availability — seat available | capacity = 2, enrolled = 1 | `REGISTERED` | ECP-08 |
| FR-08 | Availability — full | capacity = 2, enrolled = 2 | `WAITLISTED` | ECP-09 |
| FR-05 | Duplicate — already registered | target course in registered_courses | `ALREADY_REGISTERED` | ECP-10 |
| FR-02 | Course credit hours — valid class | course credits = 1 | `REGISTERED` | ECP-11 |
| FR-02 | Course credit hours — invalid, above range | course credits = 5 | `ValueError("Invalid course credits")` | ECP-12 |

The valid course-credit class is 1–4 inclusive; invalid representatives include values below 1 and above 4. The below-range representative is also exercised by BVA-05.

## A2. Boundary Value Analysis (BVA)

| Requirement | Boundary / position | Representative input | Expected output | Test ID |
|---|---|---|---|---|
| FR-01, FR-02 | Current credits at minimum | current = 0, new = 1 | `True` | BVA-01 |
| FR-01 | Current credits at maximum, addition exceeds total | current = 18, new = 1 | `False` | BVA-02 |
| FR-02 | Just below current-credit range | current = -1, new = 1 | `ValueError("Invalid current credits")` | BVA-03 |
| FR-02 | Just above current-credit range | current = 19, new = 1 | `ValueError("Invalid current credits")` | BVA-04 |
| FR-02 | Just below course-credit range | current = 0, new = 0 | `ValueError("Invalid course credits")` | BVA-05 |
| FR-02 | Lowest valid course-credit value | current = 5, new = 1 | `True` | BVA-06 |
| FR-01, FR-02 | Highest valid course-credit value; total exactly 18 | current = 14, new = 4 | `True` | BVA-07 |
| FR-02 | Just above course-credit range | current = 0, new = 5 | `ValueError("Invalid course credits")` | BVA-08 |
| FR-01 | Combined credits exactly 18 | current = 17, new = 1 | `True` | BVA-09 |
| FR-01 | Combined credits just above maximum | current = 16, new = 3 (total 19) | `False` | BVA-10 |
| FR-01 | Acceptance example, exactly 18 | current = 15, new = 3 | `True` | BVA-11 |
| FR-01 | Combined credits just below maximum | current = 16, new = 1 (total 17) | `True` | BVA-12 |
| FR-08 | One seat remains | enrolled = 2, capacity = 3 | `REGISTERED` | BVA-13 |
| FR-08 | Exactly at capacity | enrolled = 3, capacity = 3 | `WAITLISTED` | BVA-14 |
| FR-15 | Enrollment one above capacity | enrolled = 4, capacity = 3 | `ValueError("Invalid capacity or enrollment")` | BVA-15 |
| FR-15 | Capacity below minimum | capacity = 0, enrolled = 0 | `ValueError("Invalid capacity or enrollment")` | BVA-16 |
| FR-04 | Dues at zero versus just above zero | dues = 0 versus dues = 1 | `REGISTERED` versus `DUES_BLOCK` | `test_bva_dues_zero_and_one` |

## A3. Decision Table Testing

Conditions are evaluated in the FR-09 priority order: dues → duplicate → prerequisites → credit limit → availability. `—` means the condition is not reached / is irrelevant because an earlier rule determines the result.

| Rule | Dues > 0? | Already registered? | All prerequisites met? | Total credits ≤ 18? | Seat available? | Expected result |
|---|---:|---:|---:|---:|---:|---|
| R1 | Yes | — | — | — | — | `DUES_BLOCK` |
| R2 | No | Yes | — | — | — | `ALREADY_REGISTERED` |
| R3 | No | No | No | — | — | `PREREQUISITES_MISSING` |
| R4 | No | No | Yes | No | — | `CREDIT_LIMIT` |
| R5 | No | No | Yes | Yes | No | `WAITLISTED` |
| R6 | No | No | Yes | Yes | Yes | `REGISTERED` |

Executable cases:

| Test ID | Input condition / combination | Expected result |
|---|---|---|
| DT-01 | All checks pass; available seat | `REGISTERED` |
| DT-02 | All checks pass; course full | `WAITLISTED` |
| DT-03 | Positive dues | `DUES_BLOCK` |
| DT-04 | Duplicate registration | `ALREADY_REGISTERED` |
| DT-05 | Prerequisite missing | `PREREQUISITES_MISSING` |
| DT-06 | Credit total exceeds 18 | `CREDIT_LIMIT` |
| DT-07 | Dues + duplicate + missing prerequisite + full course | `DUES_BLOCK` (dues has priority) |
| DT-08 | Duplicate + missing prerequisite + full course | `ALREADY_REGISTERED` (duplicate has priority) |
| DT-09 | Missing prerequisite + credit excess + full course | `PREREQUISITES_MISSING` (prerequisites have priority) |
| DT-10 | Credit excess + full course | `CREDIT_LIMIT` (credit limit has priority) |

`registration_decision()` is also checked for non-mutation in every DT case (FR-10).

## A4. pytest Implementation and Execution

The executable tests are in `tests/test_blackbox.py`. They use plain `assert` statements and `pytest.raises()` for specified validation errors. State tests check:

- Successful registration: course added, student credits increased, course enrollment incremented (FR-11).
- Waitlisting: student ID appended once; no changes to credits, registered courses, or enrollment (FR-12).
- Rejected registration: no state mutation.
- Successful withdrawal: course removed, credits reduced, enrollment decremented (FR-13).
- Unsuccessful withdrawal: returns `False` and leaves state unchanged (FR-14).
- `registration_decision()` does not mutate state (FR-10).
- Dues validation occurs before capacity/enrollment validation (FR-15).

**Execution command:** `python -m pytest -q --tb=no`  
**Environment:** Python 3.13; pytest  
**Observed result against the supplied, unmodified starter implementation:** **34 passed, 15 failed (49 total test instances).**

The failures are retained intentionally: the SRS is the oracle, and the starter is explicitly not guaranteed to be correct. Main observed defect groups:

1. Positive dues of Rs. 1 or Rs. 5 are not blocked; implementation blocks only balances greater than Rs. 1000 (FR-04).
2. A partially completed prerequisite set is accepted (FR-03, FR-06).
3. Totals exactly equal to 18 credits are rejected (FR-01).
4. A course with `enrolled == capacity` returns `REGISTERED` rather than `WAITLISTED` (FR-08).
5. The combined priority case DT-07 returns `ALREADY_REGISTERED` instead of `DUES_BLOCK`, consistent with the incorrect dues threshold being applied before duplicate handling (FR-09).
6. Withdrawal does not decrement course enrollment (FR-13).

The exact failure list and pytest summary are preserved in `test_evidence.txt`. No implementation fixes were made, so the evidence reflects black-box testing of the original system under test.

## A5. Test Suite Optimization and Traceability

The suite uses technique-prefixed case IDs (ECP, BVA, DT) in pytest parameter IDs, allowing each execution to be traced back to its design technique and requirement. State/validation tests use ST IDs or descriptive test names.

A duplicate is defined here as the same operation with the same relevant input values and the same expected behavior—not merely two tests that happen to return the same status. The cases were compared across ECP, BVA, and decision-table groups. **No exact duplicate input scenarios were retained across those groups.** Some cases intentionally exercise the same requirement boundary or outcome using different representative values (for example, a full course in ECP, BVA, and DT), but those are not duplicates: their input values or test objective differ.

All 49 test instances are therefore kept. Consolidation is achieved through pytest parametrization and a single execution command, while the case IDs preserve technique-to-test traceability. State-transition tests remain separate because they verify mutation behavior, not only the decision status.
