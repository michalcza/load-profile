import pandas as pd
import plotly.graph_objects as go

# Load datasets
load_data = pd.read_csv('..\\wellsfargo\\LP_comma_head_202501091050_TR6919_RESULTS-LP.csv', parse_dates=['datetime'])
weather_data = pd.read_csv('..\\wellsfargo\\weather-data_84601_2023-01-08_2024-12-31.csv', parse_dates=['datetime'])

# Add a date column for aggregation
load_data['date'] = load_data['datetime'].dt.date
weather_data['date'] = weather_data['datetime'].dt.date

# Check and add sunshine duration derived columns if not present
if 'sunshine_duration_min' not in weather_data.columns:
    weather_data['sunshine_duration_min'] = weather_data['sunshine_duration_sec'] / 60
if 'sunshine_duration_hr' not in weather_data.columns:
    weather_data['sunshine_duration_hr'] = weather_data['sunshine_duration_sec'] / 3600
if 'sunshine_duration_percent' not in weather_data.columns:
    weather_data['sunshine_duration_percent'] = (weather_data['sunshine_duration_sec'] / 86400) * 100

# Calculate daily load variation (max - min)
daily_load_variation = load_data.groupby('date')['total_kw'].agg(['max', 'min'])
daily_load_variation['variation'] = daily_load_variation['max'] - daily_load_variation['min']
daily_load_variation.reset_index(inplace=True)

# Calculate daily weather metrics
daily_weather_metrics = weather_data.groupby('date').agg({
    'temperature_f': ['max', 'min'],
    'precipitation_in': 'sum',
    'cloud_cover_percent': 'mean',
    'sunshine_duration_sec': 'mean',
    'sunshine_duration_min': 'mean',
    'sunshine_duration_hr': 'mean',
    'sunshine_duration_percent': 'mean'
})
daily_weather_metrics.columns = [
    'temp_max', 'temp_min', 'precip_total',
    'cloud_cover_avg', 'sunshine_duration_avg_sec',
    'sunshine_duration_avg_min', 'sunshine_duration_avg_hr',
    'sunshine_duration_avg_percent'
]
daily_weather_metrics['temp_variation'] = daily_weather_metrics['temp_max'] - daily_weather_metrics['temp_min']
daily_weather_metrics.reset_index(inplace=True)

# Scale precipitation and sunshine duration for better visualization
precip_scale_factor = 10
sunshine_scale_factor = 0.02778
daily_weather_metrics['precip_total_scaled'] = daily_weather_metrics['precip_total'] * precip_scale_factor
daily_weather_metrics['sunshine_duration_scaled'] = daily_weather_metrics['sunshine_duration_avg_sec'] * sunshine_scale_factor

# Merge load and weather metrics
combined_metrics = pd.merge(daily_load_variation, daily_weather_metrics, on='date')

# Calculate correlations
corr_temp = combined_metrics['variation'].corr(combined_metrics['temp_variation'])
corr_precip = combined_metrics['variation'].corr(combined_metrics['precip_total'])
corr_cloud = combined_metrics['variation'].corr(combined_metrics['cloud_cover_avg'])
corr_sunshine = combined_metrics['variation'].corr(combined_metrics['sunshine_duration_avg_sec'])

print(f"Correlation between load variation and temperature variation: {corr_temp:.2f}")
print(f"Correlation between load variation and precipitation: {corr_precip:.2f}")
print(f"Correlation between load variation and cloud cover: {corr_cloud:.2f}")
print(f"Correlation between load variation and sunshine duration: {corr_sunshine:.2f}")

# Identify high and low correlation dates
high_corr_dates = combined_metrics[
    (abs(combined_metrics['variation'] - combined_metrics['temp_variation']) > 0.8) |
    (abs(combined_metrics['variation'] - combined_metrics['precip_total']) > 0.8) |
    (abs(combined_metrics['variation'] - combined_metrics['cloud_cover_avg']) > 0.8) |
    (abs(combined_metrics['variation'] - combined_metrics['sunshine_duration_avg_sec']) > 0.8)
]['date']

low_corr_dates = combined_metrics[
    (abs(combined_metrics['variation'] - combined_metrics['temp_variation']) < 0.2) &
    (abs(combined_metrics['variation'] - combined_metrics['precip_total']) < 0.2) &
    (abs(combined_metrics['variation'] - combined_metrics['cloud_cover_avg']) < 0.2) &
    (abs(combined_metrics['variation'] - combined_metrics['sunshine_duration_avg_sec']) < 0.2)
]['date']

# Initialize the figure
fig = go.Figure()

# Add daily load variation trace
fig.add_trace(go.Scatter(
    x=combined_metrics['date'],
    y=combined_metrics['variation'],
    mode='lines',
    name='Load Variation (kW)',
    line=dict(color='blue')
))

# Add temperature variation trace
fig.add_trace(go.Scatter(
    x=combined_metrics['date'],
    y=combined_metrics['temp_variation'],
    mode='lines',
    name='Temperature Variation (°F)',
    line=dict(color='orange', width = 1),
    yaxis='y2'
))

# Add scaled precipitation trace
fig.add_trace(go.Scatter(
    x=combined_metrics['date'],
    y=combined_metrics['precip_total_scaled'],
    mode='lines',
    name=f'Precipitation (in) x{precip_scale_factor}',
    line=dict(color='green', width = 1),
    yaxis='y2'
))

# Add scaled sunshine duration trace
fig.add_trace(go.Scatter(
    x=combined_metrics['date'],
    y=combined_metrics['sunshine_duration_scaled'],
    mode='lines',
    name=f'Sunshine Duration (%)',
    line=dict(color='yellow', width = 1),
    yaxis='y2'
))

# Add cloud cover trace
fig.add_trace(go.Scatter(
    x=combined_metrics['date'],
    y=combined_metrics['cloud_cover_avg'],
    mode='lines',
    name='Cloud Cover (%)',
    line=dict(color='purple', width = 1),
    yaxis='y2'
))

# Highlight high-correlation dates
fig.add_trace(go.Scatter(
    x=high_corr_dates,
    y=[combined_metrics.loc[combined_metrics['date'] == date, 'variation'].values[0] for date in high_corr_dates],
    mode='markers',
    name='High Correlation Dates',
    marker=dict(color='green', size=5, symbol='circle')
))

# Highlight low-correlation dates
fig.add_trace(go.Scatter(
    x=low_corr_dates,
    y=[combined_metrics.loc[combined_metrics['date'] == date, 'variation'].values[0] for date in low_corr_dates],
    mode='markers',
    name='Low Correlation Dates',
    marker=dict(color='red', size=5, symbol='x')
))

# # Add high and low vertical bars for temperature and load variations
# if not high_corr_dates.empty:
    # fig.add_vrect(
        # x0=min(high_corr_dates),
        # x1=max(high_corr_dates),
        # fillcolor="red",
        # opacity=0.2,
        # layer="below",
        # line_width=0,
        # annotation_text="High Correlation",
        # annotation_position="top left"
    # )

# if not low_corr_dates.empty:
    # fig.add_vrect(
        # x0=min(low_corr_dates),
        # x1=max(low_corr_dates),
        # fillcolor="blue",
        # opacity=0.2,
        # layer="below",
        # line_width=0,
        # annotation_text="Low Correlation",
        # annotation_position="top left"
    # )

# Update layout with dual y-axes
fig.update_layout(
    title='Daily Load Variation and Weather Correlations',
    xaxis_title='Date',
    yaxis=dict(
        title='Load Variation (kW)',
        titlefont=dict(color='blue'),
        tickfont=dict(color='blue'),
    ),
    yaxis2=dict(
        title='Weather Metrics',
        titlefont=dict(color='orange'),
        tickfont=dict(color='orange'),
        anchor='x',
        overlaying='y',
        side='right'
    ),
    legend_title='Legend',
    template='plotly_white'
)

# Show the plot
fig.show(config={"scrollZoom": True})
