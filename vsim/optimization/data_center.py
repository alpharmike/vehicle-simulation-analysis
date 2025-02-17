from itertools import product
import numpy as np

from ..utils import get_processed_metadata, manhattan_distance


class VSDataCenter:
    def __init__(self, data_file):
        self._locations = {}
        self._vehicles = {}
        self._container_orders = {}
        self._distance_matrix = None

        self._prepare_data(data_file)
        self._create_distance_matrix()

    def _prepare_data(self, data_file):
        locations_df, vehicles_df, container_orders_df = get_processed_metadata(meta_file_path=data_file)
        # Keep track of container orders by adding a delivery status
        container_orders_df['delivered'] = False

        self._locations = locations_df.set_index("location_name").to_dict("index")
        self._vehicles = vehicles_df.set_index("id").to_dict("index")
        self._container_orders = container_orders_df.set_index("co_id").to_dict("index")

    def _create_distance_matrix(self):
        """
        Calculate distance between each pair of locations
        """
        num_locations = len(self._locations)
        distance_matrix = np.zeros((num_locations, num_locations))
        locations = list(self._locations.values())
        for i, j in product(range(num_locations), range(num_locations)):
            x1, y1, x2, y2 = locations[i]['x'], locations[i]['y'], locations[j]['x'], locations[j]['y']
            distance_matrix[i, j] = manhattan_distance(x1, y1, x2, y2)

        self._distance_matrix = distance_matrix

    def get_distance(self, loc_1, loc_2):
        loc_1_idx = list(self.locations.keys()).index(loc_1)
        loc_2_idx = list(self.locations.keys()).index(loc_2)
        return self.distance_matrix[loc_1_idx][loc_2_idx]

    def toggle_order_status(self, order_id):
        self._container_orders[order_id]['delivered'] = not self._container_orders[order_id]['delivered']

    def update_vehicle_location(self, vehicle_id, location):
        self._vehicles[vehicle_id]['start_location'] = location

    def order_already_delivered(self, order_id):
        return self._container_orders[order_id]['delivered']

    def get_remaining_orders(self):
        remaining_orders = {}
        for order_id, order_data in self._container_orders.items():
            if not self.order_already_delivered(order_id):
                remaining_orders[order_id] = order_data
        return remaining_orders

    @property
    def locations(self):
        return self._locations.copy()

    @property
    def vehicles(self):
        return self._vehicles.copy()

    @property
    def container_orders(self):
        return self._container_orders.copy()

    @property
    def distance_matrix(self):
        return np.copy(self._distance_matrix)
