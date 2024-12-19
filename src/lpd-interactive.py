import os
import sys
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import argparse

#cd C:\Users\micha\GitHub\load-profile\src
#python lpd-interactive2.py ..\sample-data\22meters-736days-1470K_rows.csv --transformer_kva 75 --datetime "2024-10-08 16:45:00"

def process_csv(input_file):
    base, _ = os.path.splitext(input_file)
    load_profile_file = f"{base}_RESULTS-LP.csv"
    data = pd.read_csv(input_file)
    # data.to_csv(load_profile_file, index=False)
    return data, load_profile_file

def visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime):
    try:
        # Load the data
        data = pd.read_csv(load_profile_file)

        # Ensure the necessary columns are present
        if "datetime" in data.columns and "total_kw" in data.columns:
            # Convert 'datetime' column to datetime type
            data["datetime"] = pd.to_datetime(data["datetime"])

            # Check if target_datetime is within the dataset range
            min_datetime = data["datetime"].min()
            max_datetime = data["datetime"].max()

            # Initialize the Plotly figure
            fig = go.Figure()

        if target_datetime:
            if target_datetime < min_datetime or target_datetime > max_datetime:
                print(f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime}).")
                
                # Add a visible warning annotation to the figure
                fig.add_annotation(
                    xref="paper", yref="paper",
                    x=0.5, y=1.05,
                    text=f"Warning: The provided datetime '{target_datetime}' is outside the dataset range ({min_datetime} to {max_datetime}).",
                    showarrow=False,
                    font=dict(size=14, color="red"),
                    align="center",
                    bgcolor="yellow",
                    bordercolor="red",
                    borderwidth=2
                )
            else:
                # Add the main load trace here to make sure it renders on bottom
                fig.add_trace(go.Scatter(
                    x=data["datetime"],
                    y=data["total_kw"],
                    mode='lines',
                    line=dict(color='lightgrey', dash='solid', width=1),
                    name='Load (kW)'
                ))
                
                # Find the closest data point to the target_datetime
                closest_row = data.iloc[(data['datetime'] - target_datetime).abs().argmin()]
                closest_datetime = closest_row['datetime']
                closest_load = closest_row['total_kw']
                


                # Add a vertical line at the target_datetime
                fig.add_trace(go.Scatter(
                    x=[closest_datetime, closest_datetime],
                    y=[0, max(data['total_kw'])],
                    mode='lines',
                    line=dict(color='blue', dash='solid', width=2),
                    name='Target Datetime'
                ))

                # Add an annotation for the target_datetime
                fig.add_annotation(
                    x=closest_datetime,
                    y=closest_load,
                    text=f"Target: {closest_datetime.strftime('%Y-%m-%d %H:%M:%S')}<br>{closest_load:.2f} kW",
                    showarrow=True,
                    arrowhead=5,
                    arrowcolor='blue',
                    font=dict(size=12, color="blue"),
                    bgcolor="lightgray",
                    bordercolor="blue",
                    borderwidth=1
                )


            # Define thresholds for 85%, 100%, and 120% of transformer load
            load_85 = transformer_kva * 0.85
            load_100 = transformer_kva
            load_120 = transformer_kva * 1.2



            # Add horizontal threshold traces
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_85, load_85],
                mode='lines',
                line=dict(color='green', dash='dash', width=2),
                name='85% Load'
            ))
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_100, load_100],
                mode='lines',
                line=dict(color='orange', dash='dash', width=2),
                name='100% Load'
            ))
            fig.add_trace(go.Scatter(
                x=[data["datetime"].min(), data["datetime"].max()],
                y=[load_120, load_120],
                mode='lines',
                line=dict(color='red', dash='dash', width=2),
                name='120% Load'
            ))

            # Highlight the maximum load value
            max_row = data.loc[data['total_kw'].idxmax()]
            max_datetime = max_row['datetime']
            max_load = max_row['total_kw']

            # Add a vertical line and annotation for max load
            fig.add_trace(go.Scatter(
                x=[max_datetime, max_datetime],
                y=[0, max(data['total_kw'])],
                mode='lines',
                line=dict(color='red', dash='solid', width=2),
                name='Max Load'
            ))

            fig.add_annotation(
                x=max_datetime,
                y=max_load,
                text=f"Peak: {max_datetime.strftime('%Y-%m-%d %H:%M:%S')}<br>{closest_load:.2f} kW",
                showarrow=True,
                arrowhead=5,
                arrowcolor='red',
                font=dict(size=12, color="red"),
                bgcolor="lightgray",
                bordercolor="blue",
                borderwidth=1
            )

            # Customize layout
            fig.update_layout(
                title="Time-Based Load Profile Visualization",
                xaxis_title="Time",
                yaxis_title="Load (kW)",
                legend_title="Legend",
                #legend_subtitle="Click to turn ON/OFF",
                hovermode="x",
                template="plotly_white"
            )
            fig.add_annotation(
            xref="paper", yref="paper",  # Reference relative to the paper size
            x=1.02, y=1.01,             # Position near the legend
            text="Click to turn ON/OFF", # Subtitle text
            showarrow=False,
            font=dict(size=10, color="gray"),
            align="left"
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

    # Process the CSV file
    try:
        data, load_profile_file = process_csv(input_file)
        print(f"CSV processing complete: {load_profile_file}")
    except Exception as e:
        print(f"Unexpected error processing CSV file '{input_file}': {e}")
        sys.exit(1)

    # Transformer load analysis and visualization
    if transformer_kva > 0:
        try:
            visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime)
        except FileNotFoundError:
            print(f"Error: The file '{load_profile_file}' was not found.")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error during transformer load analysis or visualization: {e}")
            sys.exit(1)
    else:
        print("Transformer KVA not specified or is zero. Skipping analysis and visualization.")
