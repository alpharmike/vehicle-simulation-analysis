import re
from datetime import datetime
from typing import Optional

# Define the regex patterns for common elements in the logs
datetime_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
log_level_pattern = r"[A-Z]+"
vehicle_id_pattern = r"SC\d{3}"
to_id_pattern = r"TO_CO_TFTU\d{6}"
co_id_pattern = r"CO_TFTU\d{6}"
vehicle_status_pattern = r"(finished|working|waited)"
action_pattern = r"(PICK|DROP)"
tz_aware_datetime_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}"
location_pattern = r"((QC)\d{3}|(RAIL)\d{3}.\d{2,3}|(WS|YARD)\d{3}.\d{2})"
int_pattern = r"^-?\d+$"
float_pattern = r"^-?\d+(\.\d+)?$"

# Define regex to extract key information from the logs based on certain patterns
log_patterns = {
    "container_submission": re.compile(
        rf"(?P<log_time>{datetime_pattern})\s+"
        rf"(?P<log_level>{log_level_pattern})\s+"
        rf"adding TO (?P<to_id>{to_id_pattern}),\s+"
        rf"EMT (?P<submission_time>{tz_aware_datetime_pattern})"
    ),
    "init_scheduling": re.compile(
        rf"(?P<log_time>{datetime_pattern})\s+"
        rf"(?P<log_level>{log_level_pattern})\s+"
        rf"(?P<vehicle_id>{vehicle_id_pattern})\s+"
        rf"schedule\s+(\d:({to_id_pattern})#({co_id_pattern})#({action_pattern}),?)+"
    ),
    "travel_action_schedule": re.compile(
        rf"(?P<log_time>{datetime_pattern})\s+"  # Log timestamp
        rf"(?P<log_level>{log_level_pattern})\s+"  # Log level (INFO, DEBUG, ERROR, etc.)
        rf"(?P<vehicle_id>{vehicle_id_pattern})\s+starting\s+"  # Vehicle ID
        rf"(?P<to_id>{to_id_pattern})#"  # TO ID
        rf"(?P<co_id>{co_id_pattern})#"  # CO ID
        rf"(?P<action>{action_pattern}):\s+travel\s+"  # Action type
        rf"(?P<travel_start_time>{tz_aware_datetime_pattern})\s*-\s*"  # Travel start time
        rf"(?P<travel_end_time>{tz_aware_datetime_pattern}),\s*action\s+"  # Travel end time
        rf"(?P<action_start_time>{tz_aware_datetime_pattern})\s*-\s*"  # Action start time
        rf"(?P<action_end_time>{tz_aware_datetime_pattern})"  # Action end time
    ),
    "driving": re.compile(
        rf"(?P<log_time>{datetime_pattern})\s+"  # Log timestamp
        rf"(?P<log_level>{log_level_pattern})\s+"  # Log level (INFO, WARN, etc.)
        rf"(?P<vehicle_id>{vehicle_id_pattern})\s+"  # Vehicle ID
        rf"\(TO:\s+(?P<to_id>{to_id_pattern}),\s+"  # TO ID
        rf"CO:\s+(?P<co_id>{co_id_pattern}),\s+"  # CO ID
        rf"(?P<action>{action_pattern})\)\s+"  # Action type (e.g., PICK, DROP)
        rf"driving to\s+(?P<location_name>{location_pattern});\s+"  # Location name
        rf"(?P<duration_in_s>\d+)\s+s;\s+"  # Duration in seconds
        rf"(?P<distance_in_mm>\d+)\s+mm"  # Distance in millimeters
    ),
    "lane_usage": re.compile(
        rf"(?P<log_time>{datetime_pattern})\s+"  # Log timestamp
        rf"(?P<log_level>{log_level_pattern})\s+"  # Log level (DEBUG, INFO, etc.)
        rf"location\s+(?P<location_name>{location_pattern}):\s+"  # Location name
        rf"(?P<action>(using|freeing))\s+"
        rf"lane\s+(?P<lane_number>\d+)\s+for CO\s+"  # Lane number
        rf"(?P<co_id>{co_id_pattern})"  # CO ID
    ),
    "position_tracking": re.compile(
        rf"(?P<log_time>{datetime_pattern})\s+"
        rf"(?P<log_level>{log_level_pattern})\s+"
        rf"(?P<vehicle_id>{vehicle_id_pattern}) now at position\s+"
        rf"\((?P<x>\d+),\s+(?P<y>\d+)\)"
    ),
    "action": re.compile(
        rf"(?P<log_time>{datetime_pattern})\s+"  # Log timestamp
        rf"(?P<log_level>{log_level_pattern})\s+"  # Log level (INFO, DEBUG, etc.)
        rf"(?P<vehicle_id>{vehicle_id_pattern})\s+"  # Vehicle ID
        rf"\(TO:\s+(?P<to_id>{to_id_pattern}),\s+"  # TO ID
        rf"CO:\s+(?P<co_id>{co_id_pattern}),\s+"  # CO ID
        rf"(?P<action>{action_pattern})\)\s+"  # Action type (PICK, DROP)
        rf"(?P<status>{vehicle_status_pattern})\s+at\s+"  # Vehicle status (finished, working, waited)
        rf"(?P<location_name>{location_pattern})"  # Location name
        rf"(;\s+(?P<duration_in_s>\d+)\s+s)?"  # Duration in seconds
    ),
    "finish_schedule_element": re.compile(
        rf"(?P<log_time>{datetime_pattern})\s+"  # Log timestamp
        rf"(?P<log_level>{log_level_pattern})\s+"  # Log level (DEBUG, INFO, etc.)
        rf"finished expected schedule_element\s+"  # Fixed phrase
        rf"(?P<to_id>{to_id_pattern})#"  # TO ID
        rf"(?P<co_id>{co_id_pattern})#"  # CO ID
        rf"(?P<action>{action_pattern})"  # Action (PICK, DROP, etc.)
    )
}


def read_log_file(log_file_path: str) -> list[str]:
    with open(log_file_path, "r") as log_fp:
        log_lines = log_fp.readlines()

    return log_lines


def postprocess_parsed_log(raw_log_data: dict) -> dict:
    """
    Post-process extracted data from logs by adjusting data types
    :param raw_log_data: Raw dictionary representing data extracted from a log string
    :return: Post-processed data dictionary of the log
    """
    processed_log = {**raw_log_data}
    for key, value in raw_log_data.items():
        if value is None:
            processed_log[key] = value
        # Parse string date_times to datetime object
        elif re.match(datetime_pattern, value) or re.match(tz_aware_datetime_pattern, value):
            processed_log[key] = datetime.fromisoformat(value).replace(tzinfo=None)
        # Convert numerical strings to integer/float values (in our cases, distances and durations are numerical)
        elif re.match(int_pattern, value):
            processed_log[key] = int(value)
        elif re.match(float_pattern, value):
            processed_log[key] = float(value)
        else:
            processed_log[key] = value

    return processed_log


def parse_log(log: str) -> tuple[Optional[str], Optional[dict]]:
    """
    Parse the log string based on regex patterns. If the pattern matches one of the expected patterns, the name of the pattern along with the extracted data from the log will be returned. If the pattern does not match any of those
    expected, None will be returned
    :param log: A log formatted as string
    :return: (log_pattern, data) if the log matches an expected pattern. Otherwise, (None, None) will be returned.
    """
    log_pattern = None
    extracted_data = None
    for log_pattern_name, regex_compiler in log_patterns.items():
        # Check if the log string matches current regex pattern
        match = regex_compiler.match(log)
        if match:
            # Extract named groups if there's a match
            log_pattern = log_pattern_name
            extracted_data = match.groupdict()
            break

    return log_pattern, extracted_data


def get_parsed_logs(log_file_path: str):
    """
    Given a list of log lines extracted from the log file, parse and extract relevant information
    """
    logs_by_pattern = {log_pattern: [] for log_pattern in log_patterns}
    parsed_logs = []
    log_lines = read_log_file(log_file_path=log_file_path)

    for log_line in log_lines:
        log_line = log_line.strip()
        pattern, extracted_data = parse_log(log_line)
        if pattern:
            extracted_data = postprocess_parsed_log(extracted_data)
            if pattern == "init_scheduling":
                schedules = re.findall(rf"\d:(?P<to_id>{to_id_pattern})#(?P<co_id>{co_id_pattern})#(?P<action>{action_pattern})", log_line)
                extracted_data = {
                    **extracted_data,
                    "schedules": schedules
                }

            logs_by_pattern[pattern].append(extracted_data)
            parsed_logs.append((pattern, extracted_data))

    return logs_by_pattern, parsed_logs
