import json

from qubo import Q, variables, charge_variables


# Load the problem
with open("data/problem.json", "r") as file:
    problem = json.load(file)


def calculate_qubo_score(bitstring):
    score = 0

    for (var1, var2), coefficient in Q.items():

        x1 = bitstring[var1]
        x2 = bitstring[var2]

        score += coefficient * x1 * x2

    return score


def set_energy(bitstring, ev, charger, time, energy):

    weights = []

    for name, info in variables.items():

        if (
            info["type"] == "energy"
            and info["ev"] == ev
            and info["charger"] == charger
            and info["time"] == time
        ):
            weights.append(
                (info["weight"], name)
            )

    remaining = energy

    for weight, name in sorted(
        weights,
        reverse=True
    ):

        if remaining >= weight:

            bitstring[name] = 1
            remaining -= weight

    if remaining != 0:

        raise ValueError(
            f"Cannot represent {energy} kWh "
            f"for {ev} -> {charger} -> T{time}"
        )


def set_charge(bitstring, ev, charger, time):

    group = (
        ev,
        charger,
        time
    )

    if group not in charge_variables:

        raise ValueError(
            f"Invalid charging combination: "
            f"{ev} -> {charger} -> T{time}"
        )

    charge_name = charge_variables[group]

    bitstring[charge_name] = 1


def decode_solution(bitstring):

    schedule = []

    for name, info in variables.items():

        if info["type"] != "energy":
            continue

        if bitstring[name] == 0:
            continue

        schedule.append({
            "ev": info["ev"],
            "charger": info["charger"],
            "time": info["time"],
            "energy": info["weight"],
            "price": info["price"]
        })

    return schedule


def get_charge_state(
    bitstring,
    ev,
    charger,
    time
):

    group = (
        ev,
        charger,
        time
    )

    if group not in charge_variables:
        return 0

    charge_name = charge_variables[group]

    return bitstring[charge_name]


def validate_schedule(bitstring):

    errors = []

    schedule = decode_solution(bitstring)

    # Check EV conflicts
    for ev in problem["evs"]:

        for slot in problem["time_slots"]:

            active = 0

            for charger in problem["chargers"]:

                active += get_charge_state(
                    bitstring,
                    ev["id"],
                    charger["id"],
                    slot["id"]
                )

            if active > 1:

                errors.append(
                    f"{ev['id']} uses multiple chargers "
                    f"at {slot['time']}"
                )

    # Check charger conflicts
    for charger in problem["chargers"]:

        for slot in problem["time_slots"]:

            active = 0

            for ev in problem["evs"]:

                active += get_charge_state(
                    bitstring,
                    ev["id"],
                    charger["id"],
                    slot["id"]
                )

            if active > 1:

                errors.append(
                    f"{charger['id']} serves multiple EVs "
                    f"at {slot['time']}"
                )

    # Check charger capacity
    for item in schedule:

        charger = next(
            c for c in problem["chargers"]
            if c["id"] == item["charger"]
        )

        if item["energy"] > charger["power_kw"]:

            errors.append(
                f"{item['ev']} exceeds "
                f"{item['charger']} capacity"
            )

    # Check arrival and deadline
    for item in schedule:

        ev = next(
            e for e in problem["evs"]
            if e["id"] == item["ev"]
        )

        if not (
            ev["arrival"]
            <= item["time"]
            <= ev["deadline"]
        ):

            errors.append(
                f"{item['ev']} charges outside "
                f"its allowed time"
            )

    # Check exact energy
    for ev in problem["evs"]:

        total_energy = 0

        for item in schedule:

            if item["ev"] == ev["id"]:
                total_energy += item["energy"]

        if total_energy != ev["energy_required_kwh"]:

            errors.append(
                f"{ev['id']} requires "
                f"{ev['energy_required_kwh']} kWh "
                f"but gets {total_energy} kWh"
            )

    return errors


def calculate_real_cost(schedule):

    total_cost = 0

    for item in schedule:

        total_cost += (
            item["energy"]
            * item["price"]
        )

    return total_cost


def print_schedule(schedule):

    print("\nCharging Schedule")
    print("--------------------------------")

    grouped = {}

    for item in schedule:

        key = (
            item["ev"],
            item["charger"],
            item["time"]
        )

        grouped[key] = (
            grouped.get(key, 0)
            + item["energy"]
        )

    total_energy = 0
    total_cost = 0

    for (
        ev,
        charger,
        time
    ), energy in grouped.items():

        slot = next(
            s for s in problem["time_slots"]
            if s["id"] == time
        )

        cost = (
            energy
            * slot["price_per_kwh"]
        )

        total_energy += energy
        total_cost += cost

        print(
            f"{ev} -> "
            f"{charger} -> "
            f"{slot['time']} -> "
            f"{energy} kWh -> "
            f"₹{cost}"
        )

    print("--------------------------------")
    print(
        "Total Energy:",
        total_energy,
        "kWh"
    )
    print(
        "Total Cost: ₹",
        total_cost
    )


def create_classical_bitstring():

    # Start with all variables disabled
    bitstring = {
        name: 0
        for name in variables
    }

    # EV1 -> C2 -> 09:00 -> 3 kWh
    set_charge(
        bitstring,
        "EV1",
        "C2",
        2
    )

    set_energy(
        bitstring,
        "EV1",
        "C2",
        2,
        3
    )

    # EV1 -> C2 -> 10:00 -> 11 kWh
    set_charge(
        bitstring,
        "EV1",
        "C2",
        3
    )

    set_energy(
        bitstring,
        "EV1",
        "C2",
        3,
        11
    )

    # EV2 -> C2 -> 08:00 -> 11 kWh
    set_charge(
        bitstring,
        "EV2",
        "C2",
        1
    )

    set_energy(
        bitstring,
        "EV2",
        "C2",
        1,
        11
    )

    # EV3 -> C1 -> 09:00 -> 7 kWh
    set_charge(
        bitstring,
        "EV3",
        "C1",
        2
    )

    set_energy(
        bitstring,
        "EV3",
        "C1",
        2,
        7
    )

    # EV3 -> C1 -> 10:00 -> 7 kWh
    set_charge(
        bitstring,
        "EV3",
        "C1",
        3
    )

    set_energy(
        bitstring,
        "EV3",
        "C1",
        3,
        7
    )

    return bitstring


# Create the known classical solution
bitstring = create_classical_bitstring()


print("Real QUBO Evaluation")
print("--------------------------------")
print(
    "Binary variables:",
    len(bitstring)
)


score = calculate_qubo_score(bitstring)

schedule = decode_solution(bitstring)

errors = validate_schedule(bitstring)

cost = calculate_real_cost(schedule)


print("QUBO Score:", score)
print("Real Cost: ₹", cost)

print_schedule(schedule)


print("\nValidation")
print("--------------------------------")


if errors:

    print("INVALID")

    for error in errors:
        print("-", error)

else:

    print("VALID")