
"""Hostel room allocation with validation and basic reporting."""

import os
import secrets

import yaml
from flask import Flask, request
from markupsafe import escape

rooms = {}
allocations = {}
waitlist = []
app = Flask(__name__)

CONFIG = """
blocks:
  A: {gender: M, rooms: 3, capacity: 2, fee: 4000}
  B: {gender: F, rooms: 2, capacity: 3, fee: 3500}
"""


def load_config(text=CONFIG):
    """Load hostel configuration and initialize rooms."""
    config = yaml.safe_load(text)
    rooms.clear()
    allocations.clear()
    waitlist.clear()

    for block, info in config["blocks"].items():
        for number in range(1, info["rooms"] + 1):
            rooms[f"{block}{number}"] = {
                "gender": info["gender"],
                "capacity": info["capacity"],
                "fee": info["fee"],
                "occupants": [],
            }
    return config


def allocate_room(student_id, name, gender, year, preferred=None):
    """Allocate a suitable room to a student."""
    if not isinstance(year, int) or isinstance(year, bool):
        return None
    if student_id in allocations:
        return allocations[student_id]["room"]

    preferred = preferred or []
    room_order = list(dict.fromkeys(preferred + list(rooms.keys())))

    for room_no in room_order:
        room = rooms.get(room_no)
        if room is None:
            continue
        if room["gender"] != gender:
            continue
        if len(room["occupants"]) >= room["capacity"]:
            continue

        room["occupants"].append(student_id)
        allocations[student_id] = {
            "name": name,
            "room": room_no,
            "year": year,
        }
        if student_id in waitlist:
            waitlist.remove(student_id)
        return room_no

    if student_id not in waitlist:
        waitlist.append(student_id)
    return None


def vacate_room(student_id):
    """Remove a student from their assigned room."""
    allocation = allocations.pop(student_id, None)
    if allocation is None:
        return False

    room = rooms.get(allocation["room"])
    if room and student_id in room["occupants"]:
        room["occupants"].remove(student_id)
    return True


def monthly_fee(student_id, days_stayed):
    """Calculate the accommodation fee for a student's stay."""
    if student_id not in allocations or days_stayed < 0:
        return None

    room = rooms[allocations[student_id]["room"]]
    months = (days_stayed + 29) // 30
    return months * room["fee"]


def priority_order(students):
    """Sort students by academic year, with seniors first."""
    return sorted(
        students,
        key=lambda student: student["year"],
        reverse=True,
    )


def room_lottery(student_ids):
    """Return student IDs in securely randomized order."""
    return secrets.SystemRandom().sample(
        student_ids,
        len(student_ids),
    )


def vacant_beds():
    """Count unoccupied beds across all hostel rooms."""
    return sum(
        room["capacity"] - len(room["occupants"])
        for room in rooms.values()
    )


def connect_warden_db():
    """Prepare warden database settings from an environment variable."""
    password = os.getenv("WARDEN_DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "Set the WARDEN_DB_PASSWORD environment variable."
        )
    return sqlite_connect(
        host="localhost",
        user="warden",
        password=password,
    )


def sqlite_connect(host, user, password):
    """Return a demonstration database connection status."""
    return {
        "host": host,
        "user": user,
        "connected": bool(password),
    }


@app.route("/room")
def room_lookup():
    """Display the room allocation for a requested student."""
    student_id = request.args.get("id", "")
    allocation = allocations.get(student_id)
    return (
        f"<h1>Room for {escape(student_id)}: "
        f"{escape(str(allocation))}</h1>"
    )


def run_portal():
    """Start the Flask hostel portal with debugging disabled."""
    app.run(debug=False)


def main():
    """Run a demonstration of hostel room allocation."""
    load_config()
    print("Rooms:", list(rooms.keys()))
    print("S1 ->", allocate_room("S1", "Arjun", "M", 1))
    print("S2 ->", allocate_room("S2", "Kabir", "M", 2))
    print("S3 ->", allocate_room("S3", "Rohan", "M", 3))
    print("S4 (female) ->", allocate_room("S4", "Diya", "F", 1))
    print("S1 again ->", allocate_room("S1", "Arjun", "M", 1))
    print("S5 year '2' ->", allocate_room("S5", "Vikram", "M", "2"))
    print("Occupants of A1:", rooms["A1"]["occupants"])
    vacate_room("S2")
    print("Occupants of A1 after S2 left:", rooms["A1"]["occupants"])
    print("Fee for S1, 45 days:", monthly_fee("S1", 45))

    students = [{"year": 1}, {"year": 4}, {"year": 2}]
    priority_years = [student["year"] for student in priority_order(students)]
    print("Priority (seniors first?):", priority_years)
    print("Lottery:", room_lottery(["S6", "S7", "S8"]))
    print("Vacant beds:", vacant_beds())
    print("Waitlist:", waitlist)


if __name__ == "__main__":
    main()
