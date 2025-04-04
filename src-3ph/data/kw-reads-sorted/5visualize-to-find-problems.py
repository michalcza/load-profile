import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.io as pio

pio.renderers.default = "browser"

# Expected interval between reads (adjust if needed)
expected_interval = timedelta(minutes=15)
gap_threshold = expected_interval * 1.5  # Define how much of a gap is too large

# Load meter data
meter_data = defaultdict(list)

# Load meter-data.csv to map meter ID → name (sta)
meter_id_to_name = {}
try:
    with open('../../meter-data.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meter_id = row['meter'].strip()
            name = row['sta'].strip().lower()
            meter_id_to_name[meter_id] = name
except Exception as e:
    print(f"[ERROR] Failed to load meter-data.csv: {e}")
    meter_id_to_name = {}

for file in Path('./').rglob('all-*.csv'):
    print(f"[INFO] Reading: {file}")
    with open(file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meter = row.get('meter')
            if not meter:
                continue
            try:
                ts = datetime.strptime(row['Start Time'], "%m/%d/%y %H:%M:%S")
                meter_data[meter].append({
                    'start_time': ts,
                    'record_no': int(row['Record No.']),
                    'mw_del': float(row['mw_del']),
                    'mw_rec': float(row['mw_rec']),
                    'mva_del': float(row['mva_del']),
                    'mva_rec': float(row['mva_rec']),
                })
            except Exception:
                continue

# Plot
fig = go.Figure()
offset_step = 5
base_offset = 5

for meter_id, records in sorted(meter_data.items()):
    if not records:
        continue
    records.sort(key=lambda r: r['start_time'])
    timestamps = [r['start_time'] for r in records]

    for metric in ['mw_del', 'mw_rec', 'mva_del', 'mva_rec']:
        values = [r[metric] + base_offset for r in records]
        display_name = meter_id_to_name.get(meter_id, meter_id)  # fallback to raw meter ID
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=values,
            name=f"{display_name} - {metric}",
            mode='lines',
    ))


    # Detect gaps in Start Time
    missing_gaps = []
    for i in range(1, len(records)):
        t_prev = records[i - 1]['start_time']
        t_curr = records[i]['start_time']
        if t_curr - t_prev > gap_threshold:
            missing_gaps.append((t_prev + expected_interval, t_curr))

    # Shade missing intervals with vrects
    # fig.add_vrect(
        # x0=start, x1=end,
        # fillcolor="rgba(255, 0, 0, 0.15)",
        # layer="below", line_width=0,
        # annotation=dict(
            # text=f"Missing: {name}",
            # textangle=90,
            # font=dict(size=9),
            # xanchor="left",
            # yanchor="top"
        # )
# )

    for start, end in missing_gaps:
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="rgba(255, 0, 0, 0.15)",
            layer="below",
            line_width=0,
            annotation=dict(
                text=f"Missing: {name}",
                textangle=90,
                font=dict(size=10),
                xanchor="left",
                yanchor="top"
            )
        )
    

    base_offset += offset_step

# Layout
fig.update_layout(
    title="All Meters Load Profile with Missing Reads Highlighted",
    xaxis_title="Start Time",
    yaxis_title="Offset Power (MW/MVA)",
    height=800,
    hovermode="x unified"
)

fig.show()

