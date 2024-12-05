def visualize_load_profile_interactive(load_profile_file, transformer_kva):
    """
    Generates an interactive time-based plot using Plotly with load thresholds.
    
    Parameters:
        load_profile_file (str): Path to the CSV file containing load profile data.
        transformer_kva (float): Transformer rating in kVA.
        
    The CSV file should contain at least two columns:
        - 'datetime': Timestamps of the load measurements.
        - 'total_kw': Load in kW.
    """
    try:
        # Load the data
        data = pd.read_csv(load_profile_file)

        # Ensure the necessary columns are present
        if "datetime" in data.columns and "total_kw" in data.columns:
            # Convert 'datetime' column to datetime type
            data["datetime"] = pd.to_datetime(data["datetime"])

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
                name='Load (kW)'
            ))

            # Add horizontal lines for thresholds
            fig.add_shape(
                type="line",
                x0=data["datetime"].min(),
                x1=data["datetime"].max(),
                y0=load_85,
                y1=load_85,
                line=dict(color='orange', dash='dash'),
                name='85% Load'
            )
            fig.add_shape(
                type="line",
                x0=data["datetime"].min(),
                x1=data["datetime"].max(),
                y0=load_100,
                y1=load_100,
                line=dict(color='green', dash='dash'),
                name='100% Load'
            )
            fig.add_shape(
                type="line",
                x0=data["datetime"].min(),
                x1=data["datetime"].max(),
                y0=load_120,
                y1=load_120,
                line=dict(color='red', dash='dash'),
                name='120% Load'
            )

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