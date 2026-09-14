import json
from collections import defaultdict


def load_data():
    with open("data/small_problem.json", "r") as f:
        return json.load(f)


def add_term(Q, var1, var2, value):
    if var1 > var2:
        var1, var2 = var2, var1

    Q[(var1, var2)] += value


def add_squared_constraint(Q, expression, target, penalty):

    variables = list(expression.items())

    for var, coefficient in variables:

        linear_value = (
            coefficient * coefficient
            - 2 * target * coefficient
        )

        add_term(
            Q,
            var,
            var,
            penalty * linear_value
        )

    for i in range(len(variables)):

        var1, coefficient1 = variables[i]

        for j in range(i + 1, len(variables)):

            var2, coefficient2 = variables[j]

            quadratic_value = (
                2 * coefficient1 * coefficient2
            )

            add_term(
                Q,
                var1,
                var2,
                penalty * quadratic_value
            )


def build_qubo():

    data = load_data()

    time_slots = data["time_slots"]
    chargers = data["chargers"]
    evs = data["evs"]

    Q = defaultdict(float)

    CONSTRAINT_PENALTY = 100

    variables = []

    for e, ev in enumerate(evs):

        for c, charger in enumerate(chargers):

            for t, slot in enumerate(time_slots):

                for r in range(
                    charger["power_kw"] + 1
                ):

                    variable = (
                        f"x_{e}_{c}_{t}_{r}"
                    )

                    variables.append(variable)

    # Exactly one energy level
    for e in range(len(evs)):

        for c in range(len(chargers)):

            for t in range(len(time_slots)):

                expression = {}

                for r in range(
                    chargers[c]["power_kw"] + 1
                ):

                    variable = (
                        f"x_{e}_{c}_{t}_{r}"
                    )

                    expression[variable] = 1

                add_squared_constraint(
                    Q,
                    expression,
                    target=1,
                    penalty=CONSTRAINT_PENALTY
                )

    # Charger conflict
    for c in range(len(chargers)):

        for t in range(len(time_slots)):

            for e1 in range(len(evs)):

                for e2 in range(e1 + 1, len(evs)):

                    for r1 in range(
                        1,
                        chargers[c]["power_kw"] + 1
                    ):

                        for r2 in range(
                            1,
                            chargers[c]["power_kw"] + 1
                        ):

                            var1 = (
                                f"x_{e1}_{c}_{t}_{r1}"
                            )

                            var2 = (
                                f"x_{e2}_{c}_{t}_{r2}"
                            )

                            add_term(
                                Q,
                                var1,
                                var2,
                                CONSTRAINT_PENALTY
                            )

    # EV conflict
    for e in range(len(evs)):

        for t in range(len(time_slots)):

            for c1 in range(len(chargers)):

                for c2 in range(c1 + 1, len(chargers)):

                    for r1 in range(
                        1,
                        chargers[c1]["power_kw"] + 1
                    ):

                        for r2 in range(
                            1,
                            chargers[c2]["power_kw"] + 1
                        ):

                            var1 = (
                                f"x_{e}_{c1}_{t}_{r1}"
                            )

                            var2 = (
                                f"x_{e}_{c2}_{t}_{r2}"
                            )

                            add_term(
                                Q,
                                var1,
                                var2,
                                CONSTRAINT_PENALTY
                            )

    # Arrival and deadline
    for e, ev in enumerate(evs):

        for c, charger in enumerate(chargers):

            for t, slot in enumerate(time_slots):

                if (
                    slot["id"] < ev["arrival"]
                    or slot["id"] > ev["deadline"]
                ):

                    for r in range(
                        1,
                        charger["power_kw"] + 1
                    ):

                        variable = (
                            f"x_{e}_{c}_{t}_{r}"
                        )

                        add_term(
                            Q,
                            variable,
                            variable,
                            CONSTRAINT_PENALTY
                        )

    # Exact energy requirement
    for e, ev in enumerate(evs):

        expression = {}

        for c, charger in enumerate(chargers):

            for t in range(len(time_slots)):

                for r in range(
                    charger["power_kw"] + 1
                ):

                    variable = (
                        f"x_{e}_{c}_{t}_{r}"
                    )

                    expression[variable] = r

        add_squared_constraint(
            Q,
            expression,
            target=ev["energy_required_kwh"],
            penalty=CONSTRAINT_PENALTY
        )

    # Electricity cost
    for e in range(len(evs)):

        for c, charger in enumerate(chargers):

            for t, slot in enumerate(time_slots):

                price = slot["price_per_kwh"]

                for r in range(
                    1,
                    charger["power_kw"] + 1
                ):

                    variable = (
                        f"x_{e}_{c}_{t}_{r}"
                    )

                    cost = r * price

                    add_term(
                        Q,
                        variable,
                        variable,
                        cost
                    )

    print("\nSmall QUBO")
    print("--------------------------------")
    print(f"Binary variables: {len(variables)}")
    print(f"QUBO terms: {len(Q)}")

    return Q, variables


if __name__ == "__main__":

    Q, variables = build_qubo()

    print("\nQUBO successfully created.")