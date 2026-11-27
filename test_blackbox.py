"""Black-box tests derived exclusively from REQUIREMENTS.md (FR-01..FR-15).

Technique traceability:
- ECP cases: ECP-01..ECP-12
- BVA cases: BVA-01..BVA-15
- Decision-table cases: DT-01..DT-10
- State/validation cases: ST-01..ST-08

The pytest IDs are the case IDs used in the assignment report.  Cases are kept
input-distinct across techniques; no identical test scenario is executed twice.
"""
import pytest

from registration import (
    Student,
    Course,
    check_credit_limit,
    prerequisites_satisfied,
    registration_decision,
    register_course,
    withdraw_course,
)


def snapshot(student, course):
    """Capture all mutable state relevant to registration/withdrawal."""
    return (
        set(student.registered_courses),
        student.current_credits,
        course.enrolled,
        list(course.waitlist),
    )


# ---------------------------------------------------------------------------
# A1 — Equivalence Class Partitioning
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id, student_kwargs, course_kwargs, expected",
    [
        # Dues: zero is valid/non-blocking; any positive amount blocks (FR-04).
        ("ECP-01", {"outstanding_dues": 0}, {}, "REGISTERED"),
        ("ECP-02", {"outstanding_dues": 1}, {}, "DUES_BLOCK"),
        # Negative dues are an invalid equivalence class (FR-15).
        ("ECP-03", {"outstanding_dues": -1}, {}, "ValueError"),
        # Prerequisites: empty set and all required completed are valid.
        ("ECP-04", {"completed_courses": set()}, {"prerequisites": set()}, "REGISTERED"),
        ("ECP-05", {"completed_courses": {"CS101", "MATH101"}},
         {"prerequisites": {"CS101", "MATH101"}}, "REGISTERED"),
        # Some or none completed are both missing-prerequisite classes (FR-03, FR-06).
        ("ECP-06", {"completed_courses": {"CS101"}},
         {"prerequisites": {"CS101", "MATH101"}}, "PREREQUISITES_MISSING"),
        ("ECP-07", {"completed_courses": set()},
         {"prerequisites": {"CS101"}}, "PREREQUISITES_MISSING"),
        # Availability classes: a seat remains / course is full.
        ("ECP-08", {}, {"capacity": 2, "enrolled": 1}, "REGISTERED"),
        ("ECP-09", {}, {"capacity": 2, "enrolled": 2}, "WAITLISTED"),
        # Already registered class.
        ("ECP-10", {"registered_courses": {"CS201"}}, {}, "ALREADY_REGISTERED"),
        # Valid course credit range and invalid below/above range (FR-02).
        ("ECP-11", {}, {"credit_hours": 1}, "REGISTERED"),
        ("ECP-12", {}, {"credit_hours": 5}, "ValueError"),
    ],
)
def test_ecp_registration_classes(case_id, student_kwargs, course_kwargs, expected):
    student = Student("S001", **student_kwargs)
    # Keep course code/credit_hours defaults unless overridden by a case.
    course = Course(
        "CS201",
        course_kwargs.get("credit_hours", 3),
        course_kwargs.get("capacity", 30),
        enrolled=course_kwargs.get("enrolled", 0),
        prerequisites=course_kwargs.get("prerequisites", set()),
    )
    if expected == "ValueError":
        with pytest.raises(ValueError):
            registration_decision(student, course)
    else:
        assert registration_decision(student, course) == expected


# ---------------------------------------------------------------------------
# A2 — Boundary Value Analysis
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id, current, new, expected",
    [
        ("BVA-01", 0, 1, True),       # lower valid current-credit boundary
        ("BVA-02", 18, 1, False),     # upper valid current-credit boundary + addition
        ("BVA-03", -1, 1, "ValueError"),
        ("BVA-04", 19, 1, "ValueError"),
        ("BVA-05", 0, 0, "ValueError"),   # just below course-credit range
        ("BVA-06", 5, 1, True),           # lowest valid course credit at a distinct current load
        ("BVA-07", 14, 4, True),          # highest valid course credit, total 18
        ("BVA-08", 0, 5, "ValueError"),    # just above course-credit range
        ("BVA-09", 17, 1, True),           # combined total exactly 18
        ("BVA-10", 16, 3, False),         # combined total 19
        ("BVA-11", 15, 3, True),          # acceptance example: exactly 18
        ("BVA-12", 16, 1, True),          # one below the combined maximum (17)
    ],
)
def test_bva_credit_boundaries(case_id, current, new, expected):
    if expected == "ValueError":
        with pytest.raises(ValueError):
            check_credit_limit(current, new)
    else:
        assert check_credit_limit(current, new) is expected


@pytest.mark.parametrize(
    "case_id, enrolled, capacity, expected",
    [
        ("BVA-13", 2, 3, "REGISTERED"),  # one seat remaining
        ("BVA-14", 3, 3, "WAITLISTED"),   # exactly full
        ("BVA-15", 4, 3, "ValueError"),   # one above capacity is invalid
        ("BVA-16", 0, 0, "ValueError"),   # capacity below minimum
    ],
)
def test_bva_capacity_boundaries(case_id, enrolled, capacity, expected):
    student = Student("S002")
    course = Course("EE201", 3, capacity, enrolled=enrolled)
    if expected == "ValueError":
        with pytest.raises(ValueError):
            registration_decision(student, course)
    else:
        assert registration_decision(student, course) == expected


def test_bva_dues_zero_and_one():
    # Separate from ECP cases: verifies the exact threshold around zero.
    assert registration_decision(
        Student("S003", outstanding_dues=0), Course("MA201", 2, 10)
    ) == "REGISTERED"
    assert registration_decision(
        Student("S004", outstanding_dues=1), Course("MA202", 2, 10)
    ) == "DUES_BLOCK"


# ---------------------------------------------------------------------------
# A3 — Decision table and priority testing
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case_id, student_kwargs, course_kwargs, expected",
    [
        # Each distinct terminal outcome.
        ("DT-01", {"current_credits": 2}, {}, "REGISTERED"),
        ("DT-02", {}, {"capacity": 1, "enrolled": 1}, "WAITLISTED"),
        ("DT-03", {"outstanding_dues": 5}, {}, "DUES_BLOCK"),
        ("DT-04", {"registered_courses": {"CS201"}}, {}, "ALREADY_REGISTERED"),
        ("DT-05", {}, {"prerequisites": {"CS101"}}, "PREREQUISITES_MISSING"),
        ("DT-06", {"current_credits": 18}, {}, "CREDIT_LIMIT"),
        # Priority interactions: first applicable rule wins (FR-09).
        ("DT-07", {"outstanding_dues": 5, "registered_courses": {"CS201"}},
         {"prerequisites": {"CS101"}, "capacity": 1, "enrolled": 1}, "DUES_BLOCK"),
        ("DT-08", {"registered_courses": {"CS201"}},
         {"prerequisites": {"CS101"}, "capacity": 1, "enrolled": 1}, "ALREADY_REGISTERED"),
        ("DT-09", {"current_credits": 18},
         {"prerequisites": {"CS101"}, "capacity": 1, "enrolled": 1}, "PREREQUISITES_MISSING"),
        ("DT-10", {"current_credits": 18},
         {"capacity": 1, "enrolled": 1}, "CREDIT_LIMIT"),
    ],
)
def test_decision_table_and_priority(case_id, student_kwargs, course_kwargs, expected):
    student = Student("S005", **student_kwargs)
    course = Course(
        "CS201",
        3,
        course_kwargs.get("capacity", 30),
        enrolled=course_kwargs.get("enrolled", 0),
        prerequisites=course_kwargs.get("prerequisites", set()),
    )
    before = snapshot(student, course)
    assert registration_decision(student, course) == expected
    # FR-10: decision evaluation itself must never mutate either object.
    assert snapshot(student, course) == before


# ---------------------------------------------------------------------------
# A4 — State transitions, non-mutation, and validation
# ---------------------------------------------------------------------------

def test_successful_registration_updates_all_required_state():
    student = Student("S010", current_credits=15)
    course = Course("CS301", 3, 10, enrolled=4)
    assert register_course(student, course) == "REGISTERED"
    assert "CS301" in student.registered_courses
    assert student.current_credits == 18
    assert course.enrolled == 5


def test_waitlisting_adds_student_once_and_does_not_change_enrollment_state():
    student = Student("S011")
    course = Course("CS302", 3, 1, enrolled=1)
    assert register_course(student, course) == "WAITLISTED"
    assert course.waitlist == ["S011"]
    assert snapshot(student, course) == (set(), 0, 1, ["S011"])
    # A repeated waitlist request must not append a duplicate student ID.
    assert register_course(student, course) == "WAITLISTED"
    assert course.waitlist == ["S011"]


@pytest.mark.parametrize(
    "case_id, student_kwargs, course_kwargs, expected",
    [
        ("ST-01", {"outstanding_dues": 1}, {}, "DUES_BLOCK"),
        ("ST-02", {"registered_courses": {"CS401"}}, {}, "ALREADY_REGISTERED"),
        ("ST-03", {}, {"prerequisites": {"CS101"}}, "PREREQUISITES_MISSING"),
        ("ST-04", {"current_credits": 18}, {}, "CREDIT_LIMIT"),
    ],
)
def test_rejected_registration_does_not_change_state(case_id, student_kwargs, course_kwargs, expected):
    student = Student("S020", **student_kwargs)
    course = Course(
        "CS401", 3, 5,
        prerequisites=course_kwargs.get("prerequisites", set()),
    )
    before = snapshot(student, course)
    assert register_course(student, course) == expected
    assert snapshot(student, course) == before


def test_withdrawal_removes_course_and_reduces_credits_and_enrollment():
    student = Student("S030", current_credits=6, registered_courses={"PH101"})
    course = Course("PH101", 3, 20, enrolled=7)
    assert withdraw_course(student, course) is True
    assert "PH101" not in student.registered_courses
    assert student.current_credits == 3
    assert course.enrolled == 6


def test_withdrawal_when_not_registered_returns_false_without_mutation():
    student = Student("S031", current_credits=6)
    course = Course("PH102", 3, 20, enrolled=7)
    before = snapshot(student, course)
    assert withdraw_course(student, course) is False
    assert snapshot(student, course) == before


def test_invalid_dues_is_validated_before_invalid_capacity():
    student = Student("S032", outstanding_dues=-1)
    course = Course("PH103", 3, 0, enrolled=0)
    with pytest.raises(ValueError, match="^Invalid dues$"):
        registration_decision(student, course)


def test_invalid_capacity_or_enrollment_raises_value_error():
    with pytest.raises(ValueError, match="^Invalid capacity or enrollment$"):
        registration_decision(Student("S033"), Course("PH104", 3, 2, enrolled=3))
