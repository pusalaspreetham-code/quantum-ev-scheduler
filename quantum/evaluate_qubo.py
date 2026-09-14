import json
import itertools

from qubo import build_qubo


def load_data():
    with open("data/small_problem.json", "r") as f:
        return json.load(f)


def calculate_qubo_score(Q, variables, bitstring):

    values = {
        variables[i]: int(bitstring[i])
        for i in range(len(variables))
    }

    score = 0

    for (var1, var2), coefficient in Q.items():

        score += (
            coefficient
            * values[var1]
            * values[var2]
        )

    return score


def decode_solution(data, variables, bitstring):

    evs = data["evs"]
    chargers = data["chargers"]
    time_slots = data["time_slots"]

    schedule = []

    for i, variable in enumerate(variables):

        if bitstring[i] != "1":
            continue

        parts = variable.split("_")

        e = int(parts[1])
        c = int(parts[2])
        t = int(parts[3])
        r = int(parts[4])

        if r == 0:
            continue

        schedule.append({
            "ev": evs[e]["id"],
            "charger": chargers[c]["id"],
            "time": time_slots[t]["time"],
            "energy": r,
            "price_per_kwh": time_slots[t]["price_per_kwh"],
            "cost": r * time_slots[t]["price_per_kwh"]
        })

    return schedule


def calculate_cost(schedule):

    return sum(
        item["cost"]
        for item in schedule
    )


def main():

    print("\nExact QUBO Evaluation")
    print("--------------------------------")

    data = load_data()

    Q, variables = build_qubo()

    num_variables = len(variables)

    print(
        f"\nTesting {2 ** num_variables} "
        f"possible bitstrings..."
    )

    best_bitstring = None
    best_score = float("inf")

    # Test every possible binary assignment
    for bits in itertools.product(
        ["0", "1"],
        repeat=num_variables
    ):

        bitstring = "".join(bits)

        score = calculate_qubo_score(
            Q,
            variables,
            bitstring
        )

        if score < best_score:

            best_score = score
            best_bitstring = bitstring

    print("\nExact optimal result:")
    print("--------------------------------")

    print(
        "Bitstring:",
        best_bitstring
    )

    print(
        "QUBO score:",
        best_score
    )

    schedule = decode_solution(
        data,
        variables,
        best_bitstring
    )

    print("\nDecoded charging schedule:")
    print("--------------------------------")

    for item in schedule:

        print(
            f"{item['ev']} -> "
            f"{item['charger']} -> "
            f"{item['time']} -> "
            f"{item['energy']} kWh -> "
            f"₹{item['cost']}"
        )

    total_cost = calculate_cost(schedule)

    print("\nTotal electricity cost:")
    print("--------------------------------")
    print(f"₹{total_cost}")

    print("\nExact QUBO evaluation completed.")


if __name__ == "__main__":
    main()