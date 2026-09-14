import itertools

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from qubo import build_qubo


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

    # ---------------------------------------------
    # 1. Initial superposition
    # ---------------------------------------------

    for q in range(num_qubits):
        qc.h(q)

    # ---------------------------------------------
    # 2. Cost layer
    # ---------------------------------------------

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

    # ---------------------------------------------
    # 3. Mixer layer
    # ---------------------------------------------

    for q in range(num_qubits):

        qc.rx(
            2 * beta,
            q
        )

    # ---------------------------------------------
    # 4. Measurement
    # ---------------------------------------------

    qc.measure(
        range(num_qubits),
        range(num_qubits)
    )

    return qc


def run_qaoa(Q, variables, gamma, beta, shots=256):

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

    print("\nOptimizing QAOA parameters")
    print("--------------------------------")

    best_score = float("inf")
    best_gamma = None
    best_beta = None
    best_bitstring = None

    # Try several gamma values
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

    # Try several beta values
    beta_values = [
        0.05,
        0.10,
        0.20,
        0.30,
        0.50,
        0.70,
        1.00
    ]

    total_tests = (
        len(gamma_values)
        * len(beta_values)
    )

    print(
        f"Testing {total_tests} "
        f"parameter combinations..."
    )

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

    print("\nBest parameters:")
    print("--------------------------------")

    print(
        "Gamma:",
        best_gamma
    )

    print(
        "Beta:",
        best_beta
    )

    print(
        "Best QUBO score:",
        best_score
    )

    print(
        "Best bitstring:",
        best_bitstring
    )

    return (
        best_gamma,
        best_beta,
        best_score,
        best_bitstring
    )


def main():

    print("\nQAOA Parameter Optimization")
    print("--------------------------------")

    Q, variables = build_qubo()

    print(
        f"\nQubits: {len(variables)}"
    )

    (
        gamma,
        beta,
        score,
        bitstring
    ) = optimize_parameters(
        Q,
        variables
    )

    print("\nFinal QAOA run")
    print("--------------------------------")

    final_score, final_bitstring = run_qaoa(
        Q,
        variables,
        gamma,
        beta,
        shots=1024
    )

    print(
        "Gamma:",
        gamma
    )

    print(
        "Beta:",
        beta
    )

    print(
        "Bitstring:",
        final_bitstring
    )

    print(
        "QUBO score:",
        final_score
    )

    print("\nQAOA optimization completed.")


if __name__ == "__main__":
    main()