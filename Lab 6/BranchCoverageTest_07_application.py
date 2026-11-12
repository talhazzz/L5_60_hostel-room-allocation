import pytest

from hospital_triage_priority import (
    process_triage_wards,
    monitor_oxygen_manifolds,
)


def test_invalid_wards_type():
    with pytest.raises(ValueError):
        process_triage_wards("invalid", 10)


def test_negative_default_acuity():
    with pytest.raises(ValueError):
        process_triage_wards([], -1)


def test_empty_wards_list():
    result = process_triage_wards([], 10)
    assert result == {
        "acuity_score": 0,
        "status": "NO_URGENT_CASES",
    }


def test_non_accepting_ward():
    wards = [
        {
            "is_accepting": False,
            "patients": [{"spo2": 98, "hr": 72}],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["status"] == "NO_URGENT_CASES"


def test_accepting_ward_with_empty_patients():
    wards = [
        {
            "is_accepting": True,
            "patients": [],
            "icu_standby": False,
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["status"] == "NO_URGENT_CASES"


def test_normal_patient():
    wards = [
        {
            "is_accepting": True,
            "tier": "general",
            "patients": [{"spo2": 98, "hr": 75, "unconscious": False}],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["acuity_score"] == 10


def test_low_spo2_patient():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 85, "hr": 75, "unconscious": False}],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["acuity_score"] == 60


def test_high_heart_rate_patient():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 98, "hr": 130, "unconscious": False}],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["acuity_score"] == 60


def test_invalid_spo2():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 0, "hr": 75}],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["status"] == "NO_URGENT_CASES"


def test_invalid_heart_rate():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 98, "hr": 0}],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["status"] == "NO_URGENT_CASES"


def test_unconscious_general_ward_patient():
    wards = [
        {
            "is_accepting": True,
            "tier": "general",
            "patients": [{"spo2": 98, "hr": 75, "unconscious": True}],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["acuity_score"] == 100


def test_unconscious_outpatient_patient():
    wards = [
        {
            "is_accepting": True,
            "tier": "outpatient",
            "patients": [
                {"spo2": 98, "hr": 75, "unconscious": True},
                {"spo2": 98, "hr": 75, "unconscious": False},
            ],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["acuity_score"] == 0


def test_icu_standby_enabled():
    wards = [
        {
            "is_accepting": True,
            "icu_standby": True,
            "patients": [],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["acuity_score"] == 25


def test_icu_standby_disabled():
    wards = [
        {
            "is_accepting": True,
            "icu_standby": False,
            "patients": [],
        }
    ]
    result = process_triage_wards(wards, 10)
    assert result["acuity_score"] == 0


def test_ward_alert_more_than_four_invalid_entries():
    patients = [{"spo2": 0, "hr": 75} for _ in range(5)]
    wards = [{"is_accepting": True, "patients": patients}]
    result = process_triage_wards(wards, 10)
    assert result["status"] == "WARD_ALERT"


def test_four_invalid_entries_no_ward_alert():
    patients = [{"spo2": 0, "hr": 75} for _ in range(4)]
    wards = [{"is_accepting": True, "patients": patients}]
    result = process_triage_wards(wards, 10)
    assert result["status"] == "NO_URGENT_CASES"


def test_default_acuity_zero():
    wards = [
        {
            "is_accepting": True,
            "patients": [{"spo2": 98, "hr": 75, "unconscious": False}],
        }
    ]
    result = process_triage_wards(wards, 0)
    assert result["acuity_score"] == 0
    assert result["status"] == "NO_URGENT_CASES"


def test_empty_sensor_streams():
    assert monitor_oxygen_manifolds([]) == "NO_DATA"


def test_empty_individual_manifold():
    assert monitor_oxygen_manifolds([[], [5.0, 4.8]]) == "PRESSURE_NORMAL"


def test_normal_pressure():
    assert monitor_oxygen_manifolds([[5.0, 4.8, 4.5]]) == "PRESSURE_NORMAL"


def test_single_low_pressure_reading():
    assert monitor_oxygen_manifolds([[3.5, 4.5]]) == "PRESSURE_NORMAL"


def test_two_consecutive_low_readings():
    assert monitor_oxygen_manifolds([[3.5, 3.8]]) == "PRESSURE_FAILURE"


def test_pressure_recovery_resets_streak():
    assert monitor_oxygen_manifolds([[3.5, 4.5, 3.8, 4.2]]) == "PRESSURE_NORMAL"


def test_failure_in_later_manifold():
    streams = [[3.5, 4.5], [5.0, 3.8, 3.5]]
    assert monitor_oxygen_manifolds(streams) == "PRESSURE_FAILURE"
