from ortools.linear_solver import pywraplp

from .data_center import VSDataCenter


class VSSolver:
    """
    Solves an optimization problem based on the provided metadata on locations, vehicles, and container orders
    Objective:
        Minimize the total distance travelled per vehicle for each container assignment
    Constraints:
        Ensure all resources (vehicles) are associated with at least one order to increase throughput
        Ensure each order is assigned to exactly one vehicle
        Ensure each vehicle is assigned to one order at a time (But in general, one vehicle will be responsible for multiple container orders)
        Ensure number of vehicles dispatched to a location not exceed its capacity (in case of infeasibility of the problem, this constraint will be relaxed)
    Goal:
        We would like to analyze the impact of this optimization on
            - waiting times
            - vehicles' travelled distances
            - case durations
    """
    def __init__(self, data_center):
        self._data_center: VSDataCenter = data_center

        self._solver = None
        self._var_x = None

        self._opt_obj = None
        self._opt_x = None

        self._capacity_violation_factor = 1.0
        self._opt_results = []

    def _build_model(self):
        self._solver = pywraplp.Solver.CreateSolver('SCIP')

        self._create_variables()
        self._create_objective()
        self._create_constraints()

    def optimize(self):
        status = None
        self._capacity_violation_factor = 1.0

        while status != pywraplp.Solver.OPTIMAL:
            self._build_model()
            self._solver.SetTimeLimit(20000)
            status = self._solver.Solve()
            # Relax location capacity constraint if optimization is infeasible
            self._capacity_violation_factor *= 2
        self._opt_obj = self._solver.Objective().Value()
        self._opt_x = []
        for (v, o) in self._var_x:
            if self._var_x[v, o].solution_value() == 1:
                self._opt_x.append((v, o))

        self._opt_results.append((self._opt_x.copy(), self._opt_obj))

    def update_environment(self):
        """
        After each run of the optimization:
            1. Update the status of orders to 'delivered'
            2. Update the location of vehicles to the final destination of the associated orders
        """
        for (v, o) in self._opt_x:
            # Remove already handled orders
            self._data_center.toggle_order_status(o)

            # Update vehicle locations to the destination of previously assigned orders
            self._data_center.update_vehicle_location(v, self._data_center.container_orders[o]['dest'])

    def _create_variables(self):
        vehicles = self._data_center.vehicles
        orders = self._data_center.get_remaining_orders()

        # This will contain all combinations of (vehicle, order) pairs
        # If the assigned value for a pair is 1, that means the vehicle is assigned to that specific order
        # Otherwise, there;s no association between the order and the vehicle
        self._var_x = {}
        for v in vehicles:
            for o in orders:
                self._var_x[v, o] = self._solver.IntVar(0, 1, f'x[{v},{o}]')

    def _create_objective(self):
        vehicles = self._data_center.vehicles
        orders = self._data_center.get_remaining_orders()

        obj_expr = []
        for v, v_data in vehicles.items():
            for o, o_data in orders.items():
                v_loc = v_data['start_location']
                o_origin = o_data['origin']
                o_dest = o_data['dest']

                v_to_origin = self._data_center.get_distance(v_loc, o_origin)
                origin_to_dest = self._data_center.get_distance(o_origin, o_dest)

                obj_expr.append((v_to_origin + origin_to_dest) * self._var_x[v, o])

        # Minimize the total travelled distance for all (order, vehicle) pairs
        self._solver.Minimize(self._solver.Sum(obj_expr))

    def _create_constraints(self):
        locations = self._data_center.locations
        vehicles = self._data_center.vehicles
        orders = self._data_center.get_remaining_orders()

        # C1: Ensure all resources are associated with an order to increase throughput
        self._solver.Add(
            self._solver.Sum(self._var_x[v, o] for v in vehicles for o in orders) == min(len(vehicles), len(orders))
        )

        # C2: Each order must be assigned to at most one vehicle
        for o in orders:
            self._solver.Add(
                self._solver.Sum(self._var_x[v, o] for v in vehicles) <= 1
            )

        # C3: Each vehicle must be assigned to at most one order
        for v in vehicles:
            self._solver.Add(
                self._solver.Sum(self._var_x[v, o] for o in orders) <= 1
            )

        # C4: Number of vehicles dispatched to a location should not exceed its capacity
        for loc, loc_data in locations.items():
            expr_1 = [
                self._var_x[v, o]
                for v in vehicles
                for o in orders
                if orders[o]['origin'] == loc
            ]
            self._solver.Add(
                self._solver.Sum(expr_1) <= loc_data['capacity'] * self._capacity_violation_factor
            )

            expr_2 = [
                self._var_x[v, o]
                for v in vehicles
                for o in orders
                if orders[o]['dest'] == loc
            ]
            self._solver.Add(
                self._solver.Sum(expr_2) <= loc_data['capacity'] * self._capacity_violation_factor
            )

    def opt_ended(self):
        remaining_orders = self._data_center.get_remaining_orders()
        return len(remaining_orders) == 0

    @property
    def opt_obj(self):
        return self._opt_obj

    @property
    def opt_x(self):
        return self._opt_x

    @property
    def opt_results(self):
        return self._opt_results
