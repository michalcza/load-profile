import pandas as pd
def process_csv(input_file):
    try:
        print(f"Processing file: {input_file}")
        csv_data = pd.read_csv(input_file)
        print("CSV file read successfully.")
        peak_load = 781.92
        max_load_per_meter = csv_data.groupby('meter')['kw'].max()
        total_connected_load_corrected = max_load_per_meter.sum()
        demand_factor_corrected = peak_load / total_connected_load_corrected
        print(f"Corrected Total Connected Load: {total_connected_load_corrected}")
        print(f"Corrected Demand Factor: {demand_factor_corrected}")
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
input_file = "./LP_comma_head_202410231511.csv"
process_csv(input_file)
