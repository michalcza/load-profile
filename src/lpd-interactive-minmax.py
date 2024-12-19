import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import argparse

#cd C:\Users\micha\GitHub\load-profile\src
#python lpd-interactive2.py ..\sample-data\22meters-736days-1470K_rows_RESULTS-LP.csv --transformer_kva 75 --datetime "2024-10-08 16:45:00"

def process_csv(input_file):
    base, _ = os.path.splitext(input_file)
    load_profile_file = f"{base}_RESULTS-LP.csv"
    data = pd.read_csv(input_file)
    data.to_csv(load_profile_file, index=False)
    return data, load_profile_file

# def process_csv_no_load(input_file):
    # base, _ = os.path.splitext(input_file)
    # no_load_file = f"{base}_NO-LOAD.csv"
    # print(f"Attempting to read file: {no_load_file}")
    # if not os.path.exists(no_load_file):
        # print(f"Error: File '{no_load_file}' does not exist.")
        # sys.exit(1)
        
    # no_load_data = pd.read_csv(no_load_file)
    # no_load_data.to_csv(no_load_file, index=False)
    # return data, no_load_file

def add_annotation(fig, datetime_value, load_value, color, name_prefix):
    """Add a vertical line and annotation for a specific datetime and load value."""
    fig.add_trace(go.Scatter(
        x=[datetime_value, datetime_value],
        y=[0, load_value],
        mode='lines',
        line=dict(color=color, dash='dot'),
        name=f'{name_prefix} Line',
        visible='legendonly'
    ))
    fig.add_trace(go.Scatter(
        x=[datetime_value],
        y=[load_value],
        mode='markers+text',
        text=[f"{datetime_value.strftime('%Y-%m-%d %H:%M:%S')}<br>{load_value:.2f} kW"],
        textposition="top center",
        marker=dict(color=color, size=10),
        name=f'{name_prefix} Annotation',
        visible='legendonly'
    ))

def annotate_events(fig, data):
    """Group sequential events and annotate each event on the graph."""
    no_load['datetime'] = pd.to_datetime(no_load['datetime'])

    # Identify sequential events by grouping consecutive rows with gaps in time
    no_load['event_id'] = (no_load['datetime'].diff() > pd.Timedelta('1 hour')).cumsum()

    # Group by event and annotate
    events = no_load.groupby('event_id')
    for event_id, group in events:
        start_time = group['datetime'].min()
        end_time = group['datetime'].max()
        midpoint = start_time + (end_time - start_time) / 2
        event_text = f"Event {event_id}: {len(group)} rows\n{start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}"

        fig.add_trace(go.Scatter(
            x=[midpoint],
            y=[group['total_kw'].mean()],
            mode='markers+text',
            text=[event_text],
            textposition="top center",
            marker=dict(color='orange', size=10),
            name=f'Event {event_id} Annotation',
            visible='legendonly'
        ))

def visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime):
#def visualize_load_profile_interactive(load_profile_file, no_load_file, transformer_kva, target_datetime):
    try:
        # Load the data
        data = pd.read_csv(load_profile_file)
        print(f"Columns in the file: {data.columns.tolist()}")
        #no_load_data = pd.read_csv(no_load_file)
        if "date" in data.columns and "time" in data.columns and "kw" in data.columns:
            data['datetime'] = pd.to_datetime(data['date'] + ' ' + data['time'])
            data = data.rename(columns={'kw': 'total_kw'})
            data = data[['datetime', 'total_kw']]
        else:
            raise ValueError("Required columns ('date', 'time', 'kw') are not present in the file.")


        # Ensure the necessary columns are present
        #if "datetime" in data.columns and "total_kw" in data.columns:
        if "meter" in data.columns and "date" in data.columns and "time" in data.columns and "kw" in data.columns:

            # Convert 'datetime' column to datetime type
            data["datetime"] = pd.to_datetime(data["datetime"])

            # Aggregate data to daily min and max
            data["date"] = data["datetime"].dt.date
            daily_stats = data.groupby("date").agg(min_load=("total_kw", "min"), max_load=("total_kw", "max")).reset_index()

            # Define thresholds for 85%, 100%, and 120% of transformer load
            load_85 = transformer_kva * 0.85
            load_100 = transformer_kva
            load_120 = transformer_kva * 1.2

            # Create a Plotly figure
            fig = go.Figure()

            # Add the main load trace
            fig.add_trace(go.Scatter(
                x=data["datetime"],
                y=data["total_kw"],
                mode='lines',
                name='Load (kW)',
                visible='legendonly'
            ))

            # Add daily min and max traces
            fig.add_trace(go.Scatter(
                x=daily_stats["date"],
                y=daily_stats["min_load"],
                mode='lines+markers',
                name='Daily Min Load',
                line=dict(color='blue', dash='dot'),
                visible='legendonly'
            ))
            fig.add_trace(go.Scatter(
                x=daily_stats["date"],
                y=daily_stats["max_load"],
                mode='lines+markers',
                name='Daily Max Load',
                line=dict(color='red', dash='dot'),
                visible='legendonly'
            ))

            # Add horizontal threshold traces
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_85, load_85],
                mode='lines',
                line=dict(color='orange', dash='dash'),
                name='85% Load',
                visible='legendonly'
            ))
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_100, load_100],
                mode='lines',
                line=dict(color='green', dash='dash'),
                name='100% Load',
                visible='legendonly'
            ))
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_120, load_120],
                mode='lines',
                line=dict(color='red', dash='dash'),
                name='120% Load',
                visible='legendonly'
            ))

            # Highlight the target datetime if specified
            if target_datetime:
                # Find the closest data point to the specified datetime
                closest_row = data.iloc[(data['datetime'] - target_datetime).abs().argmin()]
                closest_datetime = closest_row['datetime']
                closest_load = closest_row['total_kw']
                add_annotation(fig, closest_datetime, closest_load, 'blue', 'Target Datetime')

            # Highlight the maximum load value
            max_row = data.loc[data['total_kw'].idxmax()]
            max_datetime = max_row['datetime']
            max_load = max_row['total_kw']
            add_annotation(fig, max_datetime, max_load, 'purple', 'Max Load')

            # Annotate sequential events from no-load data
            annotate_events(fig, no_load_data)

            # Customize layout
            fig.update_layout(
                title="Time-Based Load Profile Visualization",
                xaxis_title="Time",
                yaxis_title="Load (kW)",
                legend_title="Legend",
                hovermode="x",
                template="plotly_white"
            )

            # Show the interactive plot
            fig.show()
        else:
            print("Error: Required columns 'datetime' and 'total_kw' are not present in the file.")
    except Exception as e:
        print(f"An error occurred while generating the interactive visualization: {e}")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process a CSV file for load profile analysis.")
    parser.add_argument("filename", type=str, help="Path to the input CSV file")
    parser.add_argument("--transformer_kva", type=float, default=0, help="Transformer size in kVA")
    parser.add_argument("--datetime", type=str, help="DateTime for total load calculation (format: YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()

    input_file = args.filename
    transformer_kva = args.transformer_kva
    target_datetime = args.datetime

    # Validate file existence
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        sys.exit(1)


    # Validate datetime argument
    if target_datetime:
        try:
            target_datetime = datetime.strptime(target_datetime, "%Y-%m-%d %H:%M:%S")
            print(f"Valid datetime provided: {target_datetime}")
        except ValueError:
            print(f"Error: Invalid datetime format '{args.datetime}'. Use 'YYYY-MM-DD HH:MM:SS'.")
            sys.exit(1)

    # Process the CSV files
    try:
        data, load_profile_file = process_csv(input_file)
        #no_load_data, no_load_file = process_csv_no_load(no_load_file)
        #no_load_data, no_load_file = process_csv_no_load(input_file)

        #print(f"CSV processing complete: {load_profile_file} and {no_load_file}")
    except Exception as e:
        print(f"Unexpected error processing CSV files: {e}")
        sys.exit(1)

    # Transformer load analysis and visualization
    if transformer_kva > 0:
        try:
            #visualize_load_profile_interactive(load_profile_file, no_load_file, transformer_kva, target_datetime)
            visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime)

        except FileNotFoundError:
            print(f"Error: One of the processed files was not found.")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error during transformer load analysis or visualization: {e}")
            sys.exit(1)
    else:
        print("Transformer KVA not specified or is zero. Skipping analysis and visualization.")
