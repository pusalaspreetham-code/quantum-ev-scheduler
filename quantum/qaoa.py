import itertools
import json

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

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


def create_qaoa_circuit(
    Q,
    variables,
    gamma,
    beta
):

    num_qubits = len(variables)

    qc = QuantumCircuit(
        num_qubits,
        num_qubits
    )

    # Initial superposition
    for q in range(num_qubits):
        qc.h(q)

    # Cost layer
    for (var1, var2), coefficient in Q.items():

        q1 = variables.index(var1)
        q2 = variables.index(var2)

        if q1 == q2:

            qc.rz(
                2 * gamma * coefficient,
                q1
            )

        else:

            qc.rzz(
                2 * gamma * coefficient,
                q1,
                q2
            )

    # Mixer layer
    for q in range(num_qubits):

        qc.rx(
            2 * beta,
            q
        )

    # Measurement
    qc.measure(
        range(num_qubits),
        range(num_qubits)
    )

    return qc


def run_qaoa(
    Q,
    variables,
    gamma,
    beta,
    shots=1024
):

    circuit = create_qaoa_circuit(
        Q,
        variables,
        gamma,
        beta
    )

    simulator = AerSimulator()

    result = simulator.run(
        circuit,
        shots=shots
    ).result()

    counts = result.get_counts()

    best_score = float("inf")
    best_bitstring = None

    for measured_bitstring in counts:

        bitstring = measured_bitstring[::-1]

        score = calculate_qubo_score(
            Q,
            variables,
            bitstring
        )

        if score < best_score:

            best_score = score
            best_bitstring = bitstring

    return best_score, best_bitstring


def optimize_parameters(Q, variables):

    gamma_values = [
        0.01,
        0.05,
        0.10,
        0.20,
        0.30,
        0.50,
        0.70,
        1.00
    ]

    beta_values = [
        0.05,
        0.10,
        0.20,
        0.30,
        0.50,
        0.70,
        1.00
    ]

    best_score = float("inf")
    best_gamma = None
    best_beta = None
    best_bitstring = None

    for gamma, beta in itertools.product(
        gamma_values,
        beta_values
    ):

        score, bitstring = run_qaoa(
            Q,
            variables,
            gamma,
            beta,
            shots=256
        )

        if score < best_score:

            best_score = score
            best_gamma = gamma
            best_beta = beta
            best_bitstring = bitstring

    return (
        best_gamma,
        best_beta,
        best_score,
        best_bitstring
    )


def decode_bitstring(
    data,
    variables,
    bitstring
):

    evs = data["evs"]
    chargers = data["chargers"]
    time_slots = data["time_slots"]

    schedule = []

    for i, bit in enumerate(bitstring):

        if bit != "1":
            continue

        variable = variables[i]

        parts = variable.split("_")

        e = int(parts[1])
        c = int(parts[2])
        t = int(parts[3])
        energy = int(parts[4])

        # x(...,0) means no charging
        if energy == 0:
            continue

        price = time_slots[t]["price_per_kwh"]

        cost = energy * price

        schedule.append({
            "ev": evs[e]["id"],
            "charger": chargers[c]["id"],
            "time": time_slots[t]["time"],
            "energy": energy,
            "price_per_kwh": price,
            "cost": cost
        })

    return schedule


def print_schedule(schedule):

    print("\nQAOA Charging Schedule")
    print("--------------------------------")

    total_energy = 0
    total_cost = 0

    for item in schedule:

        print(
            f"{item['ev']} -> "
            f"{item['charger']} -> "
            f"{item['time']} -> "
            f"{item['energy']} kWh -> "
            f"₹{item['cost']}"
        )

        total_energy += item["energy"]
        total_cost += item["cost"]

    print("--------------------------------")

    print(
        f"Total Energy: {total_energy} kWh"
    )

    print(
        f"Total Electricity Cost: ₹{total_cost}"
    )


def main():

    print("\nQAOA EV Charging Optimization")
    print("--------------------------------")

    data = load_data()

    Q, variables = build_qubo()

    print(
        f"\nQubits: {len(variables)}"
    )

    # Optimize QAOA parameters
    (
        gamma,
        beta,
        score,
        bitstring
    ) = optimize_parameters(
        Q,
        variables
    )

    print("\nBest QAOA Parameters")
    print("--------------------------------")

    print(
        f"Gamma: {gamma}"
    )

    print(
        f"Beta: {beta}"
    )

    print(
        f"QUBO Score: {score}"
    )

    print(
        f"Bitstring: {bitstring}"
    )

    # Final QAOA run
    final_score, final_bitstring = run_qaoa(
        Q,
        variables,
        gamma,
        beta,
        shots=1024
    )

    print("\nFinal QAOA Result")
    print("--------------------------------")

    print(
        f"Bitstring: {final_bitstring}"
    )

    print(
        f"QUBO Score: {final_score}"
    )

    # Decode bitstring
    schedule = decode_bitstring(
        data,
        variables,
        final_bitstring
    )

    print_schedule(schedule)

    print("\nQAOA optimization completed.")


if __name__ == "__main__":
    main()