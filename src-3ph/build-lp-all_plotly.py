import pandas as pd
import plotly.graph_objs as go
import plotly.subplots as sp
from pathlib import Path

# Directory containing individual meter load profiles
lp_dir = Path("lp")
output_file = lp_dir / "all.csv"

# Collect all CSV files excluding any with '_gaps' or 'all.csv'
csv_files = [f for f in lp_dir.glob("*.csv") if "_gaps" not in f.name and f.name != "all.csv"]

# Initialize master dataframe
combined_df = None

for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    meter_name = csv_file.stem.lower()

    if "Start Time" not in df.columns or not all(col in df.columns for col in ["MW_del", "MW_rec", "MVA_del", "MVA_rec"]):
        print(f"Skipping {csv_file.name}: missing required columns.")
        continue

    df["Start Time"] = pd.to_datetime(df["Start Time"], format="%m/%d/%y %H:%M:%S", errors="coerce")
    df = df[["Start Time", "MW_del", "MW_rec", "MVA_del", "MVA_rec"]].copy()
    df.columns = [
        "Start Time",
        f"mw_del_{meter_name}", f"mw_rec_{meter_name}",
        f"mva_del_{meter_name}", f"mva_rec_{meter_name}"
    ]

    if combined_df is None:
        combined_df = df
    else:
        combined_df = pd.merge(combined_df, df, on="Start Time", how="outer")

# Fill missing values and compute totals
if combined_df is not None:
    combined_df = combined_df.sort_values("Start Time")
    combined_df = combined_df.reset_index(drop=True)

    # Detect missing timestamps (gaps)
    time_diff = combined_df["Start Time"].diff()
    mode_freq = time_diff.mode()[0] if not time_diff.mode().empty else pd.Timedelta("15min")
    gap_indices = time_diff[time_diff > mode_freq].index
    gap_lines = combined_df.loc[gap_indices, "Start Time"].tolist()
    gap_durations = time_diff[gap_indices].astype(str).tolist()

    combined_df = combined_df.fillna(0).infer_objects(copy=False)

    mw_del_cols = [col for col in combined_df.columns if col.startswith("mw_del_")]
    mw_rec_cols = [col for col in combined_df.columns if col.startswith("mw_rec_")]
    mva_del_cols = [col for col in combined_df.columns if col.startswith("mva_del_")]
    mva_rec_cols = [col for col in combined_df.columns if col.startswith("mva_rec_")]

    combined_df["MW_total_del"] = combined_df[mw_del_cols].sum(axis=1)
    combined_df["MW_total_rec"] = combined_df[mw_rec_cols].sum(axis=1)
    combined_df["MW_net"] = combined_df["MW_total_del"] + combined_df["MW_total_rec"]

    combined_df["MVA_total_del"] = combined_df[mva_del_cols].sum(axis=1)
    combined_df["MVA_total_rec"] = combined_df[mva_rec_cols].sum(axis=1)
    combined_df["MVA_net"] = combined_df["MVA_total_del"] + combined_df["MVA_total_rec"]

    combined_df["PF_net"] = combined_df["MW_net"] / combined_df["MVA_net"]
    combined_df.loc[combined_df["MVA_net"] == 0, "PF_net"] = 0.0

    combined_df.to_csv(output_file, index=False)
    print(f"Combined load profile saved to: {output_file}")

    # Create a subplot for each meter
    num_meters = len(mw_del_cols)
    fig = sp.make_subplots(rows=num_meters + 1, cols=1, shared_xaxes=True,
                           subplot_titles=[col.replace("mw_del_", "").upper() for col in mw_del_cols] + ["TOTAL"])

    anchor_axis = "y1"
    for i, col in enumerate(mw_del_cols):
        meter = col.replace("mw_del_", "")
        rec_col = f"mw_rec_{meter}"

        del_series = combined_df[col]
        rec_series = combined_df[rec_col] if rec_col in combined_df else pd.Series([0] * len(combined_df))

        fig.add_trace(go.Scatter(x=combined_df["Start Time"], y=del_series,
                                 mode="lines", name=f"{meter.upper()} Delivered",
                                 line=dict(dash="dash", color="green")), row=i+1, col=1)

        fig.add_trace(go.Scatter(x=combined_df["Start Time"], y=-rec_series,
                                 mode="lines", name=f"{meter.upper()} Received (negated)",
                                 line=dict(dash="dot", color="red")), row=i+1, col=1)

        # Adjust y-axis ranges
        if meter == "gen":
            fig.update_yaxes(range=[-40, 0], scaleanchor=anchor_axis, scaleratio=1, row=i+1, col=1)
        elif meter in ["north", "south", "west"]:
            fig.update_yaxes(range=[-40, 40], scaleanchor=anchor_axis, scaleratio=1, row=i+1, col=1)

        for j, gap_time in enumerate(gap_lines):
            fig.add_vline(x=gap_time, line_width=1, line_dash="dot", line_color="gray", row=i+1, col=1)
            y_position = 0 if meter == "gen" else 40
            fig.add_annotation(x=gap_time, y=y_position, xref="x", yref=f"y{i+1}",
                               text=gap_durations[j], showarrow=False,
                               yanchor="top", font=dict(size=10, color="gray"))

    # Add total MW_net on bottom row
    fig.add_trace(go.Scatter(x=combined_df["Start Time"], y=combined_df["MW_net"],
                             mode="lines", name="MW_net (total)", line=dict(color="blue")),
                  row=num_meters + 1, col=1)

    fig.update_yaxes(range=[-40, 40], scaleanchor=anchor_axis, scaleratio=1, row=num_meters + 1, col=1)

    for j, gap_time in enumerate(gap_lines):
        fig.add_vline(x=gap_time, line_width=1, line_dash="dot", line_color="gray", row=num_meters + 1, col=1)
        fig.add_annotation(x=gap_time, y=40, xref="x", yref=f"y{num_meters + 1}",
                           text=gap_durations[j], showarrow=False,
                           yanchor="top", font=dict(size=10, color="gray"))

    fig.update_layout(height=300 * (num_meters + 1), width=1200,
                      title_text="Load Profile Flows per Meter and Total",
                      showlegend=True,
                      xaxis_rangeslider_visible=True)

    fig.show()
else:
    print("No valid input files found.")
