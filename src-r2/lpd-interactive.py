#!/usr/bin/env python3
"""
Interactive Load Profile Visualization (EXE-friendly)

- Enables wheel/trackpad zoom and sets drag action to 'zoom' by default.
- Writes an HTML fallback next to the CSV with the same interactive config.
- Opens the HTML in the default browser and also calls fig.show() with the config.
- Loads plotly.json from inside the one-file EXE (sys._MEIPASS) when frozen,
  otherwise from the script/EXE directory or the current working directory.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from datetime import datetime
import webbrowser

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# Prefer system browser as the renderer when possible
pio.renderers.default = "browser"

# ──────────────────────────────────────────────────────────────
# Helpers for frozen/dev path resolution
# ──────────────────────────────────────────────────────────────
def is_frozen() -> bool:
    """Return True when running from a PyInstaller one-file EXE."""
    return getattr(sys, "frozen", False) is True

def exe_dir() -> str:
    """Directory containing the running EXE (frozen) or this file (dev)."""
    return os.path.dirname(sys.executable) if is_frozen() else os.path.dirname(__file__)

def embedded_base_dir() -> str:
    """
    When frozen (one-file), PyInstaller extracts the bundle to a temp folder
    available as sys._MEIPASS. In dev mode, fall back to the file directory.
    """
    return getattr(sys, "_MEIPASS", exe_dir())

def external_path(rel: str) -> str:
    """
    Legacy helper kept for compatibility. Returns a path next to the EXE/.py.
    (We prefer find_resource(...) below for robust lookups.)
    """
    return os.path.join(exe_dir(), rel)

def find_resource(basename: str) -> str | None:
    """
    Find a bundled/static resource by name.

    Search order:
      1) sys._MEIPASS (inside one-file EXE at runtime)
      2) directory of the EXE/.py
      3) current working directory
    Returns the first existing path or None.
    """
    candidates = []
    if is_frozen():
        candidates.append(os.path.join(embedded_base_dir(), basename))
    candidates.append(os.path.join(exe_dir(), basename))
    candidates.append(os.path.join(os.getcwd(), basename))
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None

# ──────────────────────────────────────────────────────────────
# Style loading and safe defaults (prevents KeyErrors)
# ──────────────────────────────────────────────────────────────
_DEFAULT_STYLE = {
    "layout": {
        "title": "Load Profile (with Weather Overlays)",
        "xaxis": {"title": "Time"},
        "yaxis": {"title": "Total kW"},
        "legend": {"orientation": "h"},
        "margin": {"l": 60, "r": 60, "t": 60, "b": 60},
        "dragmode": "zoom",   # default drag = box-zoom
        "autosize": True,
        # "hovermode": "x unified",  # optional
    },
    "traces": {
        "main_load": {"name": "Total kW", "mode": "lines"},
        "85_load":   {"name": "85% KVA", "mode": "lines", "line": {"dash": "dot"}},
        "100_load":  {"name": "100% KVA", "mode": "lines", "line": {"dash": "dash"}},
        "120_load":  {"name": "120% KVA", "mode": "lines", "line": {"dash": "dashdot"}},
        "daily_peak":{"name": "Daily Peak", "mode": "markers+lines"},
        "cloud_cover": {"name": "Cloud Cover (%)", "mode": "lines", "yaxis": "y3"},
        "temp_peak":   {"name": "Peak Temp (°F)", "mode": "markers", "yaxis": "y2"},
        "peak_load":   {"name": "Coincidental Peak", "mode": "lines", "line": {"dash": "dash"}},
        "target_datetime": {"name": "Target", "mode": "lines", "line": {"dash": "dot"}},
    },
    "annotations": {
        "peak":   {"showarrow": True, "arrowhead": 2, "ax": 20, "ay": -40},
        "target": {"showarrow": True, "arrowhead": 2, "ax": 20, "ay": -40},
    },
}

def load_style(file_path: str | None = None) -> dict:
    """
    Load plotly.json and merge with safe defaults; also print where it came from.
    This makes it obvious whether the embedded style was actually applied.
    """
    style = {}
    resolved = file_path or find_resource("plotly.json")
    if resolved and os.path.isfile(resolved):
        try:
            with open(resolved, "r", encoding="utf-8") as f:
                style = json.load(f)
            print(f"[STYLE] plotly.json loaded from: {resolved}")
        except Exception as e:
            print(f"[WARN] Failed to read plotly.json at {resolved}: {e} (using defaults)")
            style = {}
    else:
        print("[STYLE] plotly.json not found; using built-in defaults")

    merged = _DEFAULT_STYLE.copy()
    merged["layout"] = {**_DEFAULT_STYLE.get("layout", {}), **style.get("layout", {})}
    merged["traces"] = {**_DEFAULT_STYLE.get("traces", {}), **style.get("traces", {})}
    merged["annotations"] = {**_DEFAULT_STYLE.get("annotations", {}), **style.get("annotations", {})}

    # Quick summary for verification
    try:
        lk, tk, ak = (len(merged.get("layout", {})),
                      len(merged.get("traces", {})),
                      len(merged.get("annotations", {})))
        print(f"[STYLE] merged keys -> layout:{lk} traces:{tk} ann:{ak}")
    except Exception:
        pass
    return merged

# ──────────────────────────────────────────────────────────────
# Load the merged load profile with weather data
# ──────────────────────────────────────────────────────────────
def process_csv(input_file: str) -> tuple[pd.DataFrame, str]:
    """Given the ORIGINAL input CSV, derive and load {base}_RESULTS-LP.csv."""
    base, _ = os.path.splitext(input_file)
    load_profile_file = f"{base}_RESULTS-LP.csv"
    return pd.read_csv(load_profile_file), load_profile_file

# ──────────────────────────────────────────────────────────────
# Figure construction helpers
# ──────────────────────────────────────────────────────────────
def add_traces(fig: go.Figure, data: pd.DataFrame, style: dict, transformer_kva: float) -> None:
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["total_kw"], **style["traces"]["main_load"]))
    add_transformer_thresholds(fig, data, transformer_kva, style)
    add_daily_peak_load(fig, data, style)

def add_transformer_thresholds(fig: go.Figure, data: pd.DataFrame, transformer_kva: float, style: dict) -> None:
    for pct, key in zip([0.85, 1.0, 1.2], ["85_load", "100_load", "120_load"]):
        load_level = transformer_kva * pct
        fig.add_trace(go.Scatter(
            x=[data["datetime"].min(), data["datetime"].max()],
            y=[load_level, load_level],
            **style["traces"][key]
        ))

def add_daily_peak_load(fig: go.Figure, data: pd.DataFrame, style: dict) -> None:
    if "date" not in data.columns:
        data["date"] = data["datetime"].dt.date
    daily_peak = data.loc[data.groupby("date")["total_kw"].idxmax()]
    trace_kw = style["traces"].get("daily_peak", {"mode": "markers+lines", "name": "Daily Peak"})
    fig.add_trace(go.Scatter(x=daily_peak["datetime"], y=daily_peak["total_kw"], **trace_kw))

def add_weather_traces(fig: go.Figure, data: pd.DataFrame, style: dict,
                       show_cloud_cover: bool = True, show_temp_peak: bool = True) -> None:
    if show_cloud_cover and "cloud_cover_percent" in data.columns:
        trace = dict(style["traces"]["cloud_cover"]); trace.setdefault("yaxis", "y3")
        fig.add_trace(go.Scatter(x=data["datetime"], y=data["cloud_cover_percent"], **trace))
    if show_temp_peak and "temperature_f" in data.columns:
        if "date" not in data.columns:
            data["date"] = data["datetime"].dt.date
        peak_temp_data = data.loc[data.groupby("date")["temperature_f"].idxmax()]
        trace = dict(style["traces"]["temp_peak"]); trace.setdefault("yaxis", "y2")
        fig.add_trace(go.Scatter(x=peak_temp_data["datetime"], y=peak_temp_data["temperature_f"], **trace))

def annotate_peak_load(fig: go.Figure, data: pd.DataFrame, style: dict) -> None:
    max_row = data.loc[data["total_kw"].idxmax()]
    fig.add_trace(go.Scatter(
        x=[max_row["datetime"], max_row["datetime"]],
        y=[0, max(data["total_kw"])],
        **style["traces"]["peak_load"]
    ))
    fig.add_annotation(
        x=max_row["datetime"], y=max_row["total_kw"],
        **style["annotations"]["peak"],
        text=f"Coincidental Peak:<br>{max_row['datetime'].strftime('%Y-%m-%d %H:%M')}<br>{max_row['total_kw']:.2f} kW"
    )

def handle_target_datetime(fig: go.Figure, data: pd.DataFrame, style: dict, target_datetime: str | None) -> None:
    if not target_datetime:
        return
    try:
        target_dt = pd.to_datetime(target_datetime)
        closest_row = data.iloc[(data['datetime'] - target_dt).abs().argmin()]
        fig.add_trace(go.Scatter(
            x=[closest_row['datetime'], closest_row['datetime']],
            y=[0, max(data["total_kw"])],
            **style["traces"]["target_datetime"]
        ))
        fig.add_annotation(
            x=closest_row['datetime'], y=closest_row['total_kw'],
            **style["annotations"]["target"],
            text=f"Load at target:<br>{closest_row['datetime'].strftime('%Y-%m-%d %H:%M')}<br>{closest_row['total_kw']:.2f} kW"
        )
    except Exception as e:
        print(f"[WARN] Error parsing/handling target datetime: {e}")

# ──────────────────────────────────────────────────────────────
# Main visualize routine
# ──────────────────────────────────────────────────────────────
def visualize_load_profile_interactive(load_profile_file: str, transformer_kva: float,
                                       target_datetime: str | None = None) -> None:
    try:
        print(f"[INFO] Reading merged load profile: {load_profile_file}")
        data = pd.read_csv(load_profile_file)

        if "datetime" not in data.columns or "total_kw" not in data.columns:
            raise ValueError("Required columns missing in load profile (need 'datetime' and 'total_kw').")

        data["datetime"] = pd.to_datetime(data["datetime"])
        if "date" not in data.columns:
            data["date"] = data["datetime"].dt.date

        style = load_style()  # <-- now resolves MEIPASS, exe_dir, or CWD

        fig = go.Figure()
        fig.update_layout(**style.get("layout", {}))  # includes dragmode='zoom'

        add_traces(fig, data, style, transformer_kva)
        add_weather_traces(fig, data, style)
        annotate_peak_load(fig, data, style)
        handle_target_datetime(fig, data, style, target_datetime)

        # Ensure secondary axes exist for overlays
        fig.update_layout(
            yaxis2=dict(title="Temperature (°F)", overlaying="y", side="right", position=1.0, showgrid=False),
            yaxis3=dict(title="Cloud Cover (%)", overlaying="y", side="right", position=0.95, showgrid=False, range=[-100, 200]),
        )

        # Interactive controls baked into BOTH show() and HTML
        plot_config = {
            "scrollZoom": True, "displayModeBar": True,
            "modeBarButtonsToAdd": ["zoom2d","pan2d","autoScale2d","resetScale2d","zoomIn2d","zoomOut2d"],
            "doubleClick": "reset", "staticPlot": False,
        }

        # Write HTML and try to open it
        html_path = load_profile_file.replace("_RESULTS-LP.csv", "_RESULTS-LP-INTERACTIVE.html")
        fig.write_html(html_path, include_plotlyjs="cdn", auto_open=False, config=plot_config)
        print(f"[OK] Interactive HTML written to: {html_path}")

        try:
            fig.show(config=plot_config)
        except Exception as e:
            print(f"[WARN] fig.show() failed: {e}")

        try:
            webbrowser.open("file://" + os.path.abspath(html_path))
        except Exception as e:
            print(f"[WARN] Could not open HTML in browser: {e}")

    except Exception as e:
        print(f"[ERROR] An error occurred while generating the interactive visualization: {e}")

# ──────────────────────────────────────────────────────────────
# CLI entrypoint
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a CSV file for load profile analysis.")
    parser.add_argument("filename", type=str, help="Path to the input CSV file")
    parser.add_argument("--transformer_kva", type=float, default=0, help="Transformer size in kVA")
    parser.add_argument("--datetime", type=str, help="Target DateTime (YYYY-MM-DD HH:MM:SS)")
    args = parser.parse_args()

    input_file = args.filename
    transformer_kva = args.transformer_kva
    target_datetime = args.datetime

    if not os.path.isfile(input_file):
        print(f"[ERROR] File '{input_file}' does not exist.")
        sys.exit(1)

    if target_datetime:
        try:
            target_datetime = datetime.strptime(target_datetime, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"[ERROR] Invalid datetime format '{args.datetime}'. Use 'YYYY-MM-DD HH:MM:SS'.")
            sys.exit(1)

    try:
        _data, load_profile_file = process_csv(input_file)
        if transformer_kva > 0:
            visualize_load_profile_interactive(load_profile_file, transformer_kva, target_datetime)
        else:
            print("[INFO] Transformer KVA not specified or is zero. Skipping visualization.")
    except Exception as e:
        print(f"[ERROR] Unexpected error processing CSV file '{input_file}': {e}")
        sys.exit(1)
