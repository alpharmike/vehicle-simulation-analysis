def manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def get_overlapping_processes(process_arrival_time, prev_process_intervals):
    overlapping_times = []
    for interval in prev_process_intervals:
        if interval[0] <= process_arrival_time <= interval[1]:
            overlapping_times.append(interval)

    return overlapping_times


def estimate_start_time(process_arrival_time, overlapping_intervals, loc_capacity):
    if len(overlapping_intervals) < loc_capacity:
        return process_arrival_time

    earliest_start_time = overlapping_intervals[0][1]
    for interval in overlapping_intervals[1:]:
        earliest_start_time = min(earliest_start_time, interval[1])

    return earliest_start_time


def get_vehicle_last_track(tracking_list, vehicle_id):
    for record in tracking_list:
        if record["v_id"] == vehicle_id:
            return record
