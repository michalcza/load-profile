import os
import re
from datetime import datetime

# Allowed filename keywords
allowed_keys = ['gen', 'north', 'south', 'west']
renamed_files = []
skipped_files = []

def extract_start_end_times(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        data_lines = [line for line in lines if re.match(r"^\s*\d+\s*,", line)]

        if not data_lines:
            return None, None

        start_str = data_lines[0].split(",")[2].strip()
        end_str = data_lines[-1].split(",")[3].strip()

        start_dt = datetime.strptime(start_str, "%m/%d/%y %H:%M:%S")
        end_dt = datetime.strptime(end_str, "%m/%d/%y %H:%M:%S")

        start_fmt = start_dt.strftime("%m%d%y-%H%M%S")
        end_fmt = end_dt.strftime("%m%d%y-%H%M%S")

        return start_fmt, end_fmt
    except Exception:
        return None, None

# Main logic
for filename in os.listdir():
    if filename.lower().endswith(".csv"):
        lowercase = filename.lower()
        for key in allowed_keys:
            if key in lowercase:
                start, end = extract_start_end_times(filename)
                if start and end:
                    new_filename = f"{key}-{start}_{end}.csv"
                    if os.path.exists(new_filename):
                        print(f"Skipping '{filename}': '{new_filename}' already exists.")
                        skipped_files.append((filename, new_filename))
                        break
                    try:
                        os.rename(filename, new_filename)
                        print(f"Renamed: {filename} -> {new_filename}")
                        renamed_files.append((filename, new_filename))
                    except Exception as e:
                        print(f"Error renaming '{filename}': {e}")
                break

print("\nSummary:")
print(f"Renamed: {len(renamed_files)} files")
print(f"Skipped: {len(skipped_files)} files (already exist)")
