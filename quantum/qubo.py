import json


# Load the problem
with open("data/problem.json", "r") as file:
    problem = json.load(file)


P = 1000

Q = {}
variables = {}
charge_variables = {}


def add_term(var1, var2, coefficient):
    key = tuple(sorted((var1, var2)))
    Q[key] = Q.get(key, 0) + coefficient


def add_squared_constraint(terms, target):
    # Add linear terms
    for var, coefficient in terms:
        add_term(
            var,
            var,
            P * (
                coefficient ** 2
                - 2 * target * coefficient
            )
        )

    # Add quadratic terms
    for i in range(len(terms)):

        var1, coeff1 = terms[i]

        for j in range(i + 1, len(terms)):

            var2, coeff2 = terms[j]

            add_term(
                var1,
                var2,
                2 * P * coeff1 * coeff2
            )


def get_binary_weights(max_energy):
    # Create binary weights up to charger capacity
    weights = []

    remaining = max_energy
    weight = 1

    while remaining > 0:

        current = min(weight, remaining)

        weights.append(current)

        remaining -= current
        weight *= 2

    return weights


# Create charging variables
for ev in problem["evs"]:

    for charger in problem["chargers"]:

        max_energy = charger["power_kw"]

        weights = get_binary_weights(max_energy)

        for slot in problem["time_slots"]:

            # Check arrival and deadline
            if not (
                ev["arrival"]
                <= slot["id"]
                <= ev["deadline"]
            ):
                continue

            group = (
                ev["id"],
                charger["id"],
                slot["id"]
            )

            charge_name = (
                f"{ev['id']}_"
                f"{charger['id']}_T{slot['id']}_"
                f"CHARGE"
            )

            charge_variables[group] = charge_name

            variables[charge_name] = {
                "type": "charge",
                "ev": ev["id"],
                "charger": charger["id"],
                "time": slot["id"],
                "weight": 1,
                "power": max_energy,
                "price": slot["price_per_kwh"]
            }

            # Create energy bits
            for bit, weight in enumerate(weights):

                name = (
                    f"{ev['id']}_"
                    f"{charger['id']}_T{slot['id']}_"
                    f"B{bit}"
                )

                variables[name] = {
                    "type": "energy",
                    "ev": ev["id"],
                    "charger": charger["id"],
                    "time": slot["id"],
                    "bit": bit,
                    "weight": weight,
                    "power": max_energy,
                    "price": slot["price_per_kwh"],
                    "charge_variable": charge_name
                }


# Add electricity cost
for name, info in variables.items():

    if info["type"] != "energy":
        continue

    cost = (
        info["weight"]
        * info["price"]
    )

    add_term(
        name,
        name,
        cost
    )


# Add exact energy requirement
for ev in problem["evs"]:

    terms = []

    for name, info in variables.items():

        if (
            info["type"] == "energy"
            and info["ev"] == ev["id"]
        ):

            terms.append(
                (
                    name,
                    info["weight"]
                )
            )

    add_squared_constraint(
        terms,
        ev["energy_required_kwh"]
    )


# Link energy bits with charge variable
for name, info in variables.items():

    if info["type"] != "energy":
        continue

    charge_name = info["charge_variable"]

    # Penalize energy when charging is inactive
    add_term(
        name,
        name,
        P * info["weight"]
    )

    add_term(
        name,
        charge_name,
        -P * info["weight"]
    )


# EV conflict constraint
# One EV cannot use two chargers at the same time.
for ev in problem["evs"]:

    for slot in problem["time_slots"]:

        charge_terms = []

        for charger in problem["chargers"]:

            group = (
                ev["id"],
                charger["id"],
                slot["id"]
            )

            if group in charge_variables:
                charge_terms.append(
                    charge_variables[group]
                )

        for i in range(len(charge_terms)):

            for j in range(i + 1, len(charge_terms)):

                add_term(
                    charge_terms[i],
                    charge_terms[j],
                    P
                )


# Charger conflict constraint
# One charger cannot serve two EVs at the same time.
for charger in problem["chargers"]:

    for slot in problem["time_slots"]:

        charge_terms = []

        for ev in problem["evs"]:

            group = (
                ev["id"],
                charger["id"],
                slot["id"]
            )

            if group in charge_variables:
                charge_terms.append(
                    charge_variables[group]
                )

        for i in range(len(charge_terms)):

            for j in range(i + 1, len(charge_terms)):

                add_term(
                    charge_terms[i],
                    charge_terms[j],
                    P
                )


print("Real EV Charging QUBO")
print("--------------------------------")
print("EVs:", len(problem["evs"]))
print("Chargers:", len(problem["chargers"]))
print("Time slots:", len(problem["time_slots"]))
print("Binary variables:", len(variables))
print("Charge variables:", len(charge_variables))
print("QUBO terms:", len(Q))


print("\nCharger Encoding")

for charger in problem["chargers"]:

    weights = get_binary_weights(
        charger["power_kw"]
    )

    print(
        f"{charger['id']} "
        f"({charger['power_kw']} kW) -> "
        f"{weights}"
    )


print("\nVariables by EV")

for ev in problem["evs"]:

    count = 0

    for info in variables.values():

        if info["ev"] == ev["id"]:
            count += 1

    print(
        f"{ev['id']} -> {count} binary variables"
    )


print("\nQUBO successfully created.")