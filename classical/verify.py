import json


def load_data():
    with open("data/problem.json", "r") as f:
        return json.load(f)


def verify_schedule(schedule):
    data = load_data()

    evs = data["evs"]
    chargers = data["chargers"]
    time_slots = data["time_slots"]

    errors = []

    # --------------------------------------------------
    # Check 1: EV IDs are valid
    # --------------------------------------------------

    valid_ev_ids = {ev["id"] for ev in evs}

    for item in schedule:

        if item["ev"] not in valid_ev_ids:
            errors.append(
                f"Unknown EV: {item['ev']}"
            )

    # --------------------------------------------------
    # Check 2: Charger IDs are valid
    # --------------------------------------------------

    valid_charger_ids = {
        charger["id"] for charger in chargers
    }

    for item in schedule:

        if item["charger"] not in valid_charger_ids:
            errors.append(
                f"Unknown charger: {item['charger']}"
            )

    # --------------------------------------------------
    # Check 3: Time slots are valid
    # --------------------------------------------------

    valid_times = {
        slot["time"] for slot in time_slots
    }

    for item in schedule:

        if item["time"] not in valid_times:
            errors.append(
                f"Unknown time slot: {item['time']}"
            )

    # --------------------------------------------------
    # Check 4:
    # A charger cannot serve two EVs at the same time
    # --------------------------------------------------

    charger_time_pairs = set()

    for item in schedule:

        pair = (
            item["charger"],
            item["time"]
        )

        if pair in charger_time_pairs:

            errors.append(
                f"Charger {item['charger']} "
                f"is used by multiple EVs "
                f"at {item['time']}"
            )

        charger_time_pairs.add(pair)

    # --------------------------------------------------
    # Check 5:
    # An EV cannot use two chargers at the same time
    # --------------------------------------------------

    ev_time_pairs = set()

    for item in schedule:

        pair = (
            item["ev"],
            item["time"]
        )

        if pair in ev_time_pairs:

            errors.append(
                f"{item['ev']} uses multiple chargers "
                f"at {item['time']}"
            )

        ev_time_pairs.add(pair)

    # --------------------------------------------------
    # Check 6:
    # Energy must be within charger capacity
    # --------------------------------------------------

    for item in schedule:

        charger = next(
            (
                c for c in chargers
                if c["id"] == item["charger"]
            ),
            None
        )

        if charger is None:
            continue

        energy = item["energy"]

        if energy < 0:
            errors.append(
                f"{item['ev']} has negative energy"
            )

        if energy > charger["power_kw"]:
            errors.append(
                f"{item['ev']} receives {energy} kWh "
                f"from {item['charger']}, but maximum "
                f"is {charger['power_kw']} kWh"
            )

    # --------------------------------------------------
    # Check 7:
    # EV cannot charge before arrival
    # or after deadline
    # --------------------------------------------------

    for item in schedule:

        ev = next(
            (
                e for e in evs
                if e["id"] == item["ev"]
            ),
            None
        )

        slot = next(
            (
                s for s in time_slots
                if s["time"] == item["time"]
            ),
            None
        )

        if ev is None or slot is None:
            continue

        if slot["id"] < ev["arrival"]:

            errors.append(
                f"{item['ev']} charges before arrival"
            )

        if slot["id"] > ev["deadline"]:

            errors.append(
                f"{item['ev']} charges after deadline"
            )

    # --------------------------------------------------
    # Check 8:
    # Exact energy requirement
    # --------------------------------------------------

    for ev in evs:

        total_energy = sum(
            item["energy"]
            for item in schedule
            if item["ev"] == ev["id"]
        )

        if total_energy != ev["energy_required_kwh"]:

            errors.append(
                f"{ev['id']} requires "
                f"{ev['energy_required_kwh']} kWh "
                f"but receives {total_energy} kWh"
            )

    # --------------------------------------------------
    # Check 9:
    # Charging continuity
    # --------------------------------------------------

    for ev in evs:

        ev_schedule = [
            item
            for item in schedule
            if item["ev"] == ev["id"]
            and item["energy"] > 0
        ]

        if not ev_schedule:
            continue

        charging_slots = []

        for item in ev_schedule:

            slot = next(
                (
                    s for s in time_slots
                    if s["time"] == item["time"]
                ),
                None
            )

            if slot:
                charging_slots.append(slot["id"])

        charging_slots.sort()

        for i in range(len(charging_slots) - 1):

            if (
                charging_slots[i + 1]
                != charging_slots[i] + 1
            ):

                errors.append(
                    f"{ev['id']} has a gap in charging "
                    f"between slot "
                    f"{charging_slots[i]} and "
                    f"{charging_slots[i + 1]}"
                )

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    if errors:

        print("\nSchedule is INVALID")
        print("--------------------------------")

        for error in errors:
            print("ERROR:", error)

    else:

        print("\nSchedule is VALID")
        print("--------------------------------")
        print("All constraints are satisfied.")


if __name__ == "__main__":

    schedule = [
        {
            "ev": "EV1",
            "charger": "C2",
            "time": "09:00",
            "energy": 3
        },
        {
            "ev": "EV1",
            "charger": "C2",
            "time": "10:00",
            "energy": 11
        },
        {
            "ev": "EV2",
            "charger": "C2",
            "time": "08:00",
            "energy": 11
        },
        {
            "ev": "EV3",
            "charger": "C1",
            "time": "09:00",
            "energy": 7
        },
        {
            "ev": "EV3",
            "charger": "C1",
            "time": "10:00",
            "energy": 7
        }
    ]

    verify_schedule(schedule)