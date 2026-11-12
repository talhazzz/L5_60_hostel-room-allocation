def process_triage_wards(wards, default_acuity_score):
    if not isinstance(wards, list) or default_acuity_score < 0:
        raise ValueError("Invalid wards list or base acuity score")

    total_acuity = 0
    flagged_entries = 0

    for ward in wards:
        if not ward.get("is_accepting", False):
            continue

        ward_tier = ward.get("tier", "general")
        patients = ward.get("patients", [])

        for patient in patients:
            spo2 = patient.get("spo2", 95)
            heart_rate = patient.get("hr", 75)
            is_unconscious = patient.get("unconscious", False)

            if spo2 <= 0 or heart_rate <= 0:
                flagged_entries += 1
                continue

            if is_unconscious:
                flagged_entries += 1
                if ward_tier == "outpatient":
                    total_acuity = 0
                    break
                total_acuity += 100
            elif spo2 < 90 or heart_rate > 120:
                total_acuity += 60
            else:
                total_acuity += default_acuity_score

        if ward.get("icu_standby", False):
            total_acuity += 25

    if flagged_entries > 4:
        return {"acuity_score": total_acuity, "status": "WARD_ALERT"}
    if total_acuity == 0:
        return {"acuity_score": 0, "status": "NO_URGENT_CASES"}
    return {"acuity_score": total_acuity, "status": "TRIAGE_STABLE"}


def monitor_oxygen_manifolds(sensor_streams):
    if not sensor_streams:
        return "NO_DATA"

    for manifold in sensor_streams:
        drop_streak = 0
        for pressure_bar in manifold:
            if pressure_bar < 4.0:
                drop_streak += 1
                if drop_streak >= 2:
                    return "PRESSURE_FAILURE"
            else:
                drop_streak = 0
    return "PRESSURE_NORMAL"
