import pytest
import subprocess
import os
import pandas as pd

# Define paths to all the scripts
LDP_MAIN = "lpd-main.py"
LDP_INTERACTIVE = "lpd-interactive.py"
LDP_MERGE = "lpd-merge.py"
LDP_WEATHER = "lpd-weather.py"

# Define test data and paths
TEST_CSV_FILE = "./sample-data/test_data.csv"
TEST_ZIPCODE = "84601"
TEST_START_DATE = "2024-08-04"
TEST_END_DATE = "2024-08-10"
TRANSFORMER_KVA = 75

### --- LDP-MAIN TESTS ---
def test_lpd_main_runs():
    """Test if lpd-main.py runs without error"""
    result = subprocess.run(
        ["python", LDP_MAIN, TEST_CSV_FILE, "--transformer_kva", str(TRANSFORMER_KVA)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

def test_lpd_main_creates_results_file():
    """Test if lpd-main generates the expected results file"""
    results_file = TEST_CSV_FILE.replace(".csv", "_RESULTS.txt")
    assert os.path.isfile(results_file)

def test_lpd_main_creates_results_lp_file():
    """Test if lpd-main generates the expected load profile file"""
    lp_file = TEST_CSV_FILE.replace(".csv", "_RESULTS-LP.csv")
    assert os.path.isfile(lp_file)
    
    # Check if the load profile has the expected columns
    df = pd.read_csv(lp_file)
    assert "datetime" in df.columns
    assert "total_kw" in df.columns


### --- LDP-WEATHER TESTS ---
def test_lpd_weather_runs():
    """Test if lpd-weather.py runs without error"""
    result = subprocess.run(
        ["python", LDP_WEATHER, TEST_ZIPCODE, TEST_START_DATE, TEST_END_DATE],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

def test_lpd_weather_creates_file():
    """Check if the weather file is generated"""
    weather_file = TEST_CSV_FILE.replace(".csv", "_WEATHER.csv")
    assert os.path.isfile(weather_file)

### --- LDP-MERGE TESTS ---
def test_lpd_merge_runs():
    """Test if lpd-merge.py runs and merges files correctly"""
    result = subprocess.run(
        ["python", LDP_MERGE, TEST_CSV_FILE],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

def test_lpd_merge_creates_results_lp_file():
    """Check if merge creates the _RESULTS-LP.csv"""
    lp_file = TEST_CSV_FILE.replace(".csv", "_RESULTS-LP.csv")
    assert os.path.isfile(lp_file)

### --- LDP-INTERACTIVE TESTS ---
def test_lpd_interactive_runs():
    """Test if lpd-interactive.py runs without error"""
    result = subprocess.run(
        ["python", LDP_INTERACTIVE, TEST_CSV_FILE],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

def test_lpd_interactive_creates_html():
    """Check if lpd-interactive.py creates the interactive HTML"""
    interactive_file = TEST_CSV_FILE.replace(".csv", "_INTERACTIVE_RESULTS.html")
    assert os.path.isfile(interactive_file)
