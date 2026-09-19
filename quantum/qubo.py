import json

with open("data/problem.json", "r") as file:
    problem = json.load(file)

P = 100
Q = {}
variables = {}


def add_term(var1, var2, coefficient):
    key = tuple(sorted((var1, var2)))
    Q[key] = Q.get(key, 0) + coefficient


def add_squared_constraint(terms, target):
    for var, coefficient in terms:
        add_term(
            var,
            var,
            P * (coefficient ** 2 - 2 * target * coefficient)
        )

    for i in range(len(terms)):
        var1, coeff1 = terms[i]

        for j in range(i + 1, len(terms)):
            var2, coeff2 = terms[j]

            add_term(
                var1,
                var2,
                2 * P * coeff1 * coeff2
            )


# Create possible charging decisions
for ev in problem["evs"]:
    for charger in problem["chargers"]:
        for slot in problem["time_slots"]:

            if ev["arrival"] <= slot["id"] <= ev["deadline"]:

                for energy in range(charger["power_kw"] + 1):

                    name = (
                        f"{ev['id']}_"
                        f"{charger['id']}_"
                        f"T{slot['id']}_"
                        f"E{energy}"
                    )

                    variables[name] = {
                        "ev": ev["id"],
                        "charger": charger["id"],
                        "time": slot["id"],
                        "energy": energy,
                        "price": slot["price_per_kwh"]
                    }


# Add electricity cost
for name, info in variables.items():
    cost = info["energy"] * info["price"]
    add_term(name, name, cost)


# Choose exactly one energy option for each time slot
groups = {}

for name, info in variables.items():
    key = (
        info["ev"],
        info["charger"],
        info["time"]
    )

    groups.setdefault(key, []).append(name)


for group in groups.values():
    terms = [(var, 1) for var in group]
    add_squared_constraint(terms, 1)


# Deliver the required energy
for ev in problem["evs"]:
    terms = []

    for name, info in variables.items():
        if info["ev"] == ev["id"]:
            terms.append((name, info["energy"]))

    add_squared_constraint(
        terms,
        ev["energy_required_kwh"]
    )


print("Small EV Charging QUBO")
print("--------------------------------")
print("Binary variables:", len(variables))
print("QUBO terms:", len(Q))
print("\nQUBO successfully created.")