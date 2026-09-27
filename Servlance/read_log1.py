"""
Surveillance Log Parser & Search CLI Engine

Execution:
python read_log1.py --log surveillance.log --id 1 --start "2026-09-27 07:18:00"
"""

import argparse
import re
from pathlib import Path
from datetime import datetime

def parse_time(time_str):
    """Converts input CLI strings into datetime objects for comparison."""
    if not time_str:
        return None
    
    clean_str = time_str.strip().split(",")[0]  # Remove trailing milliseconds if any
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
    
    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt)
        except ValueError:
            continue
            
    print("[Warn] Could not parse date format for: " + str(time_str) + ". Expected 'YYYY-MM-DD HH:MM:SS'.")
    return None

def parse_tracking_log(log_file_path, filter_id=None, filter_name=None, start_time=None, end_time=None):
    log_path = Path(log_file_path)
    
    if not log_path.exists():
        print("[Error] Log file not found at: " + str(log_file_path))
        return

    start_dt = parse_time(start_time)
    end_dt = parse_time(end_time)

    border = "=" * 56
    print("\n" + border)
    print("TRACK ID   | TIMESTAMP                 | YOLO CONF ")
    print(border)

    parsed_count = 0
    matched_count = 0

    # Fixed syntax template matching your layout entries cleanly
    # Pattern accounts for optional headers like [TRACK UPDATE] or [NEW TRACK] dynamically
    log_pattern = re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3} - \w+ - \[.*?\] Tracking ID:\s*(?P<id>\d+)\s*\|\s*Conf:\s*(?P<conf>\d+\.\d+)\s*\|\s*Identity:\s*(?P<name>.+)$"
    )

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            
            # Target active data rows containing our metric labels
            if "Tracking ID:" not in line_str or "|" not in line_str:
                continue
                
            match = log_pattern.match(line_str)
            if not match:
                continue

            try:
                raw_timestamp = match.group("ts")
                track_id = match.group("id")
                yolo_conf = match.group("conf")
                identity = match.group("name")

                parsed_count += 1

                # Filter 1: Track ID verification
                if filter_id and track_id != str(filter_id).strip():
                    continue
                
                # Filter 2: Name substring identification
                if filter_name and filter_name.lower() not in identity.lower():
                    continue

                # Filter 3: Time range boundary comparison ("between")
                log_dt = datetime.strptime(raw_timestamp, "%Y-%m-%d %H:%M:%S")

                if start_dt and log_dt < start_dt:
                    continue
                if end_dt and log_dt > end_dt:
                    continue

                # Clean formatted tabular output layout
                print(track_id.ljust(10) + " | " + raw_timestamp.ljust(25) + " | " + yolo_conf.ljust(10))
                matched_count += 1
                        
            except Exception as e:
                continue

    print(border)
    print("Total log records scanned: " + str(parsed_count))
    print("Matching search entries displayed: " + str(matched_count) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Surveillance Log Search CLI Engine")
    parser.add_argument("--log", type=str, default="surveillance.log", help="Path to your log file")
    parser.add_argument("--id", type=str, default=None, help="Search by Tracking ID number")
    parser.add_argument("--name", type=str, default=None, help="Search by name string")
    parser.add_argument("--start", type=str, default=None, help="Start timestamp (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--end", type=str, default=None, help="End timestamp (YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()

    parse_tracking_log(args.log, filter_id=args.id, filter_name=args.name, start_time=args.start, end_time=args.end)
