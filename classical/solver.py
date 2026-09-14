import json
from ortools.sat.python import cp_model


def load_data():
    with open("data/problem.json", "r") as f:
        return json.load(f)


def solve():
    data = load_data()

    time_slots = data["time_slots"]
    chargers = data["chargers"]
    evs = data["evs"]

    model = cp_model.CpModel()

    charge = {}
    energy = {}

    for e in range(len(evs)):
        for c in range(len(chargers)):
            for t in range(len(time_slots)):

                charge[e, c, t] = model.NewBoolVar(
                    f"charge_{e}_{c}_{t}"
                )

                energy[e, c, t] = model.NewIntVar(
                    0,
                    chargers[c]["power_kw"],
                    f"energy_{e}_{c}_{t}"
                )

    # Constraint 1:
    # An EV can use at most one charger in a time slot.
    for e in range(len(evs)):
        for t in range(len(time_slots)):

            model.Add(
                sum(
                    charge[e, c, t]
                    for c in range(len(chargers))
                ) <= 1
            )

    # Constraint 2:
    # A charger can serve only one EV in a time slot.
    for c in range(len(chargers)):
        for t in range(len(time_slots)):

            model.Add(
                sum(
                    charge[e, c, t]
                    for e in range(len(evs))
                ) <= 1
            )

    # Constraint 3:
    # Energy can only be delivered when the charger is active.
    for e in range(len(evs)):
        for c in range(len(chargers)):
            for t in range(len(time_slots)):

                model.Add(
                    energy[e, c, t]
                    <= chargers[c]["power_kw"]
                    * charge[e, c, t]
                )

    # Constraint 4:
    # Respect arrival and deadline.
    for e, ev in enumerate(evs):

        for c in range(len(chargers)):
            for t in range(len(time_slots)):

                slot_id = time_slots[t]["id"]

                if (
                    slot_id < ev["arrival"]
                    or slot_id > ev["deadline"]
                ):
                    model.Add(
                        charge[e, c, t] == 0
                    )

                    model.Add(
                        energy[e, c, t] == 0
                    )

    # Constraint 5:
    # EV must receive exactly the required energy.
    for e, ev in enumerate(evs):

        total_energy = sum(
            energy[e, c, t]
            for c in range(len(chargers))
            for t in range(len(time_slots))
        )

        model.Add(
            total_energy == ev["energy_required_kwh"]
        )

    # Constraint 6:
    # Charging must be continuous.
    for e, ev in enumerate(evs):

        arrival_index = next(
            t
            for t, slot in enumerate(time_slots)
            if slot["id"] == ev["arrival"]
        )

        deadline_index = next(
            t
            for t, slot in enumerate(time_slots)
            if slot["id"] == ev["deadline"]
        )

        for t in range(arrival_index, deadline_index):

            current_slot = sum(
                charge[e, c, t]
                for c in range(len(chargers))
            )

            next_slot = sum(
                charge[e, c, t + 1]
                for c in range(len(chargers))
            )

            model.Add(
                next_slot <= current_slot
            )

    # Objective:
    # Minimize electricity cost.
    model.Minimize(
        sum(
            energy[e, c, t]
            * time_slots[t]["price_per_kwh"]
            for e in range(len(evs))
            for c in range(len(chargers))
            for t in range(len(time_slots))
        )
    )

    solver = cp_model.CpSolver()

    status = solver.Solve(model)

    if status not in [
        cp_model.OPTIMAL,
        cp_model.FEASIBLE
    ]:
        print("No Feasible solution found")
        return

    schedule = []

    total_energy = 0
    total_cost = 0

    print("\nOptimal EV Charging Schedule")
    print("--------------------------------")

    for e, ev in enumerate(evs):

        ev_energy = 0
        ev_cost = 0

        for c, charger in enumerate(chargers):
            for t, slot in enumerate(time_slots):

                charged_energy = solver.Value(
                    energy[e, c, t]
                )

                if charged_energy > 0:

                    price = slot["price_per_kwh"]

                    cost = (
                        charged_energy * price
                    )

                    schedule.append({
                        "ev": ev["id"],
                        "charger": charger["id"],
                        "time": slot["time"],
                        "energy": charged_energy,
                        "price_per_kwh": price,
                        "cost": cost
                    })

                    ev_energy += charged_energy
                    ev_cost += cost

                    print(
                        f"{ev['id']} -> "
                        f"{charger['id']} -> "
                        f"{slot['time']} "
                        f"(Energy: {charged_energy} kWh, "
                        f"Price: ₹{price}/kWh, "
                        f"Cost: ₹{cost})"
                    )

        total_energy += ev_energy
        total_cost += ev_cost

        print(
            f"{ev['id']} Total: "
            f"{ev_energy} kWh, "
            f"₹{ev_cost}"
        )
        print()

    print("--------------------------------")
    print(f"Total Energy: {total_energy} kWh")
    print(f"Total Cost: ₹{total_cost}")

    # Save solution
    result = {
        "status": "OPTIMAL",
        "total_energy_kwh": total_energy,
        "total_cost": total_cost,
        "schedule": schedule
    }

    with open(
        "results/classical_solution.json",
        "w"
    ) as f:
        json.dump(
            result,
            f,
            indent=4
        )

    print("\nSolution saved to:")
    print("results/classical_solution.json")


if __name__ == "__main__":
    solve()