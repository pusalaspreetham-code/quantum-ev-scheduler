import json 
from ortools.sat.python import cp_model

def load_data():
    with open('data/problem.json', 'r') as f:
        data = json.load(f)
    return data

def solve():
    data=load_data()

    time_slots=data["time_slots"]
    chargers=data["chargers"]
    evs=data["evs"]

    model=cp_model.CpModel()

    x={}

    #Pushing the data into Dictonary 
    for e in range(len(evs)):
        for c in range(len(chargers)):
            for t in range(len(time_slots)):
                x[e,c,t]=model.NewBoolVar(f"x_{e}_{c}_{t}")

    #Constraint 1:Each EV can charge in exactly one charger/time slots
    for e in range(len(evs)):
        model.Add(
            sum(x[e,c,t] for c in range(len(chargers)) for t in range(len(time_slots)))==1
        )

    #Constraint 2:A charger can serve only ONE EV in a time slot.
    for c in range(len(chargers)):
        for t in range(len(time_slots)):
            model.Add(sum(x[e,c,t] for e in range(len(evs)))<=1)

    #Constraint 3: EV must use a charger powerful enough for its requirement.
    for e,ev in enumerate(evs):
        for c,charger in enumerate(chargers):
            for t in range(len(time_slots)):
                if(charger["power"]<ev["energy_required"]):
                    model.Add(x[e,c,t]==0)

    #Constraint 4:EV must finish before its deadline.
    for e, ev in enumerate(evs):
        deadline = ev["deadline"]

        for c in range(len(chargers)):
            for t in range(len(time_slots)):

                slot_id = time_slots[t]["id"]

                if slot_id > deadline:
                    model.Add(x[e, c, t] == 0)

    #Telling model to minimize price
    model.Minimize(sum(x[e,c,t]*time_slots[t]["price"] for e in range(len(evs)) for c in range(len(chargers)) for t in range(len(time_slots))))

    solver=cp_model.CpSolver()

    status=solver.Solve(model)

    if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("No Feasible solution found")
        return
    
    print("\nOptimal EV Charging Schedule")
    print("--------------------------------")

    total_cost=0

    for e, ev in enumerate(evs):
        for c, charger in enumerate(chargers):
            for t, slot in enumerate(time_slots):
                if solver.Value(x[e,c,t])==1:
                    cost=slot["price"]
                    total_cost+=cost

                    print(
                        f"{ev['id']} -> "
                        f"{charger['id']} -> "
                        f"{slot['time']} "
                        f"(Price: {cost})"
                    )
    
    print("--------------------------------")
    print(f"Total Cost: {total_cost}")


if __name__ == "__main__":
    solve()