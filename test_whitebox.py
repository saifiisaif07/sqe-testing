"""White-box structural tests for registration.py.

Expected outcomes remain requirement-derived where behavior is specified.
Monkeypatching is used only to isolate register_course's WAITLISTED state
transition, because registration_decision's preceding capacity validation
makes its enrolled > capacity branch infeasible for valid inputs.
"""
import pytest

import registration
from registration import (
    Course,
    Student,
    prerequisites_satisfied,
    registration_decision,
    register_course,
)


def test_wb01_dues_block_return_path_above_implementation_threshold():
    # WB-01: registration_decision line 51; takes dues-block return branch.
    # Rs. 1001 is positive and therefore blocked by FR-04.
    student = Student("WB01", outstanding_dues=1001)
    course = Course("WB101", 3, 10)
    assert registration_decision(student, course) == "DUES_BLOCK"


@pytest.mark.parametrize(
    "case_id, enrolled, capacity, expected_exception",
    [
        ("WB-02", -1, 2, True),   # first comparison false; chain short-circuits
        ("WB-03", 3, 2, True),    # first true, second false
        ("WB-04", 0, 0, True),    # chain true, capacity < 1 true
        ("WB-05", 0, 2, False),   # all capacity predicates valid
    ],
)
def test_wb_capacity_validation_short_circuit_paths(
    case_id, enrolled, capacity, expected_exception
):
    # WB-02..WB-05: structural paths through the compound capacity guard.
    student = Student(case_id)
    course = Course("WB102", 3, capacity, enrolled=enrolled)
    if expected_exception:
        with pytest.raises(ValueError, match="^Invalid capacity or enrollment$"):
            registration_decision(student, course)
    else:
        assert registration_decision(student, course) == "REGISTERED"


def test_wb06_empty_prerequisite_short_circuit():
    # WB-06: prerequisites_satisfied line 39 true branch; no intersection call.
    assert prerequisites_satisfied(set(), set()) is True


def test_wb07_all_prerequisites_present():
    # WB-07: prerequisites_satisfied line 41 true outcome.
    assert prerequisites_satisfied({"CS101", "MATH101"}, {"CS101", "MATH101"}) is True


def test_wb08_no_prerequisites_present():
    # WB-08: prerequisites_satisfied line 41 false outcome.
    assert prerequisites_satisfied(set(), {"CS101"}) is False


def test_wb09_waitlist_transition_adds_student_when_absent(monkeypatch):
    # WB-09: register_course line 70 true and line 71 executed.
    # The decision is stubbed solely to isolate the state-transition branch.
    student = Student("WB09")
    course = Course("WB109", 3, 1, enrolled=1)
    monkeypatch.setattr(registration, "registration_decision", lambda *_: "WAITLISTED")
    assert register_course(student, course) == "WAITLISTED"
    assert course.waitlist == ["WB09"]
    assert student.current_credits == 0
    assert student.registered_courses == set()
    assert course.enrolled == 1


def test_wb10_waitlist_transition_does_not_duplicate_student(monkeypatch):
    # WB-10: WAITLISTED is true but membership condition is false.
    student = Student("WB10")
    course = Course("WB110", 3, 1, enrolled=1, waitlist=["WB10"])
    monkeypatch.setattr(registration, "registration_decision", lambda *_: "WAITLISTED")
    assert register_course(student, course) == "WAITLISTED"
    assert course.waitlist == ["WB10"]
