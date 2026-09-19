import itertools

from qubo import Q, variables


# Calculate the QUBO score for a bitstring
def calculate_score(bitstring):
    values = dict(zip(variables.keys(), bitstring))

    score = 0

    for (var1, var2), coefficient in Q.items():
        score += coefficient * values[var1] * values[var2]

    return score


# Convert the best bitstring into a charging schedule
def decode_solution(bitstring):
    schedule = []

    for name, bit in zip(variables.keys(), bitstring):

        if bit == 1:
            info = variables[name]

            schedule.append({
                "ev": info["ev"],
                "charger": info["charger"],
                "time": info["time"],
                "energy": info["energy"],
                "price": info["price"],
                "cost": info["energy"] * info["price"]
            })

    return schedule


# Test every possible binary solution
best_bitstring = None
best_score = float("inf")

for bitstring in itertools.product([0, 1], repeat=len(variables)):

    score = calculate_score(bitstring)

    if score < best_score:
        best_score = score
        best_bitstring = bitstring


# Decode the best solution
schedule = decode_solution(best_bitstring)


print("QUBO Evaluation")
print("--------------------------------")
print("Binary variables:", len(variables))
print("Solutions tested:", 2 ** len(variables))
print("Best bitstring:", "".join(map(str, best_bitstring)))
print("Best QUBO score:", best_score)

print("\nCharging Schedule")

total_energy = 0
total_cost = 0

for item in schedule:

    print(
        f"{item['ev']} -> "
        f"{item['charger']} -> "
        f"Time Slot {item['time']} -> "
        f"{item['energy']} kWh -> "
        f"₹{item['cost']}"
    )

    total_energy += item["energy"]
    total_cost += item["cost"]


print("\nTotal Energy:", total_energy, "kWh")
print("Total Cost: ₹", total_cost)