import json

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from qubo import Q, variables


# Load the problem
with open("data/small_problem.json", "r") as file:
    problem = json.load(file)


# Calculate QUBO score
def calculate_score(bitstring):
    values = dict(zip(variables.keys(), map(int, bitstring)))

    score = 0

    for (var1, var2), coefficient in Q.items():
        score += coefficient * values[var1] * values[var2]

    return score


# Check whether the problem is feasible
def check_feasibility():

    for ev in problem["evs"]:

        max_energy = 0

        for charger in problem["chargers"]:

            for slot in problem["time_slots"]:

                if ev["arrival"] <= slot["id"] <= ev["deadline"]:
                    max_energy += charger["power_kw"]

        required_energy = ev["energy_required_kwh"]

        if max_energy < required_energy:

            print("\nProblem is infeasible")
            print("--------------------------------")
            print(
                f"{ev['id']} requires: "
                f"{required_energy} kWh"
            )
            print(
                f"Maximum possible energy: "
                f"{max_energy} kWh"
            )
            print("No valid charging schedule exists.")

            return False

    return True


# Check whether a bitstring is valid
def is_valid(bitstring):

    values = dict(
        zip(
            variables.keys(),
            map(int, bitstring)
        )
    )

    # Check exactly one option for each time slot
    groups = {}

    for name, info in variables.items():

        key = (
            info["ev"],
            info["charger"],
            info["time"]
        )

        groups.setdefault(key, []).append(name)

    for group in groups.values():

        selected = sum(
            values[name]
            for name in group
        )

        if selected != 1:
            return False

    # Check required energy for each EV
    for ev in problem["evs"]:

        total_energy = 0

        for name, info in variables.items():

            if info["ev"] == ev["id"]:

                total_energy += (
                    values[name] *
                    info["energy"]
                )

        if total_energy != ev["energy_required_kwh"]:
            return False

    return True


# Create variable-to-qubit mapping
variable_index = {
    variable: index
    for index, variable in enumerate(
        variables.keys()
    )
}


# Build QAOA circuit
def build_qaoa_circuit(gamma, beta):

    num_qubits = len(variables)

    circuit = QuantumCircuit(
        num_qubits,
        num_qubits
    )

    # Create superposition
    for qubit in range(num_qubits):
        circuit.h(qubit)

    # Apply cost layer
    for (var1, var2), coefficient in Q.items():

        q1 = variable_index[var1]
        q2 = variable_index[var2]

        if q1 == q2:

            circuit.rz(
                -gamma * coefficient,
                q1
            )

        else:

            circuit.rz(
                -gamma * coefficient / 2,
                q1
            )

            circuit.rz(
                -gamma * coefficient / 2,
                q2
            )

            circuit.rzz(
                gamma * coefficient / 2,
                q1,
                q2
            )

    # Apply mixer
    for qubit in range(num_qubits):

        circuit.rx(
            2 * beta,
            qubit
        )

    # Measure
    circuit.measure(
        range(num_qubits),
        range(num_qubits)
    )

    return circuit


# Check whether the problem can be solved
if not check_feasibility():

    raise SystemExit


# Search for QAOA parameters
best_cost = float("inf")
best_bitstring = None
best_gamma = None
best_beta = None
best_counts = None

simulator = AerSimulator()


for gamma in [
    0.05,
    0.1,
    0.2,
    0.3,
    0.5,
    0.8,
    1.0
]:

    for beta in [
        0.05,
        0.1,
        0.2,
        0.3,
        0.5,
        0.8,
        1.0
    ]:

        circuit = build_qaoa_circuit(
            gamma,
            beta
        )

        compiled = transpile(
            circuit,
            simulator
        )

        result = simulator.run(
            compiled,
            shots=1024
        ).result()

        counts = result.get_counts()

        for measured_bitstring in counts:

            bitstring = measured_bitstring[::-1]

            # Ignore invalid solutions
            if not is_valid(bitstring):
                continue

            values = dict(
                zip(
                    variables.keys(),
                    map(int, bitstring)
                )
            )

            total_cost = 0

            for name, value in values.items():

                if value == 1:

                    info = variables[name]

                    total_cost += (
                        info["energy"] *
                        info["price"]
                    )

            if total_cost < best_cost:

                best_cost = total_cost
                best_bitstring = bitstring
                best_gamma = gamma
                best_beta = beta
                best_counts = counts


# Make sure QAOA found a valid solution
if best_bitstring is None:

    print("\nQAOA did not find a valid solution.")

    raise SystemExit


# Print valid measurement results
print("\nValid Measurement Results")
print("--------------------------------")

total_shots = sum(
    best_counts.values()
)

for measured_bitstring, count in sorted(
    best_counts.items(),
    key=lambda item: item[1],
    reverse=True
):

    bitstring = measured_bitstring[::-1]

    if is_valid(bitstring):

        probability = (
            count /
            total_shots *
            100
        )

        print(
            f"{bitstring} -> "
            f"{count} shots -> "
            f"{probability:.2f}% -> "
            f"VALID"
        )


# Decode the best solution
values = dict(
    zip(
        variables.keys(),
        map(int, best_bitstring)
    )
)

schedule = []


for name, value in values.items():

    if value == 1:

        info = variables[name]

        schedule.append({
            "ev": info["ev"],
            "charger": info["charger"],
            "time": info["time"],
            "energy": info["energy"],
            "price": info["price"],
            "cost": (
                info["energy"] *
                info["price"]
            )
        })


# Print final result
print("\nQAOA EV Charging Optimization")
print("--------------------------------")
print("Qubits:", len(variables))
print("Best gamma:", best_gamma)
print("Best beta:", best_beta)
print("Best bitstring:", best_bitstring)
print(
    "Best QUBO score:",
    calculate_score(best_bitstring)
)

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


print(
    "\nTotal Energy:",
    total_energy,
    "kWh"
)

print(
    "Total Cost: ₹",
    total_cost
)