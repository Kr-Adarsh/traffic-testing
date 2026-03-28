import sys
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("traffic_log.csv") #correctly add the traffic_log.csv's path
if not csv_path.exists():
    print(f"[!] File not found: {csv_path}")
    print("    Usage: python traffic_viz.py path/to/traffic_log.csv")
    sys.exit(1)

df = pd.read_csv(csv_path, parse_dates=["timestamp_utc", "captured_at_utc"])
df["date"] = df["timestamp_utc"].dt.date

print(f"[✓] Loaded {len(df)} rows from {csv_path}")
views  = df[df["type"] == "view"].groupby("date",  as_index=False).agg(count=("count","sum"), uniques=("uniques","sum"))
print("duplicates: ",df.duplicated().sum())
clones = df[df["type"] == "clone"].groupby("date", as_index=False).agg(count=("count","sum"), uniques=("uniques","sum"))
total_views        = int(df[df["type"] == "view"]["count"].sum())
total_view_uniques = int(df[df["type"] == "view"]["uniques"].sum())
total_clones       = int(df[df["type"] == "clone"]["count"].sum())
total_clone_uniques= int(df[df["type"] == "clone"]["uniques"].sum())
date_range         = f'{df["date"].min()}  →  {df["date"].max()}'

#theme
BG      = "#0a0b0f"
SURFACE = "#111318"
BORDER  = "#1e2029"
GREEN   = "#00e5a0"
BLUE    = "#4f8cff"
PURPLE  = "#a78bfa"
ORANGE  = "#fb923c"
MUTED   = "#4a4f63"
TEXT    = "#e2e8f0"
SUBTEXT = "#8892a4"

axis_style = dict(
    gridcolor=BORDER, gridwidth=1,
    tickfont=dict(color=SUBTEXT, size=10, family="monospace"),
    linecolor=BORDER, zerolinecolor=BORDER,
)

fig = make_subplots(
    rows=3, cols=2,
    row_heights=[0.12, 0.46, 0.42],
    column_widths=[0.65, 0.35],
    specs=[
        [{"type": "indicator"}, {"type": "indicator"}],
        [{"colspan": 2},        None                 ],
        [{"type": "bar"},       {"type": "pie"}      ],
    ],
    vertical_spacing=0.06,
    horizontal_spacing=0.06,
)

for col, val, label, color in [
    (1, total_views,         f"Total Views<br><sup>{date_range}</sup>",   GREEN),
    (2, total_clones,        f"Total Clones<br><sup>{date_range}</sup>",  PURPLE),
]:
    fig.add_trace(go.Indicator(
        mode="number",
        value=val,
        title=dict(text=label, font=dict(color=SUBTEXT, size=11, family="monospace")),
        number=dict(font=dict(color=color, size=48, family="monospace"), valueformat=","),
    ), row=1, col=col)

fig.add_trace(go.Scatter(
    x=views["date"], y=views["count"],
    name="Views", mode="lines+markers",
    line=dict(color=GREEN, width=2.5),
    marker=dict(size=6, color=GREEN),
    fill="tozeroy", fillcolor="rgba(0,229,160,0.08)",
    hovertemplate="<b>%{x}</b><br>Views: %{y}<extra></extra>",
), row=2, col=1)

fig.add_trace(go.Scatter(
    x=views["date"], y=views["uniques"],
    name="Unique Visitors", mode="lines+markers",
    line=dict(color=BLUE, width=2, dash="dot"),
    marker=dict(size=5, color=BLUE),
    fill="tozeroy", fillcolor="rgba(79,140,255,0.05)",
    hovertemplate="<b>%{x}</b><br>Unique: %{y}<extra></extra>",
), row=2, col=1)

fig.add_trace(go.Scatter(
    x=clones["date"], y=clones["count"],
    name="Clones", mode="lines+markers",
    line=dict(color=PURPLE, width=2),
    marker=dict(size=5, color=PURPLE),
    hovertemplate="<b>%{x}</b><br>Clones: %{y}<extra></extra>",
), row=2, col=1)

fig.add_trace(go.Bar(
    x=clones["date"], y=clones["count"],
    name="Clones", marker_color="rgba(167,139,250,0.75)",
    marker_line_color=PURPLE, marker_line_width=1,
    hovertemplate="<b>%{x}</b><br>Clones: %{y}<extra></extra>",
), row=3, col=1)

fig.add_trace(go.Bar(
    x=clones["date"], y=clones["uniques"],
    name="Unique Cloners", marker_color="rgba(167,139,250,0.25)",
    marker_line_color=PURPLE, marker_line_width=1,
    hovertemplate="<b>%{x}</b><br>Unique: %{y}<extra></extra>",
), row=3, col=1)

fig.add_trace(go.Pie(
    labels=["Views", "Clones"],
    values=[total_views, total_clones],
    hole=0.62,
    marker=dict(colors=[GREEN, PURPLE], line=dict(color=BG, width=2)),
    textfont=dict(color=TEXT, family="monospace", size=11),
    hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>",
), row=3, col=2)

#layout
fig.update_layout(
    title=dict(
        text=f"<b>traffic.log</b>  <span style='color:{SUBTEXT};font-size:13px'>{csv_path.name}</span>",
        font=dict(color=TEXT, size=20, family="monospace"),
        x=0.02, y=0.98,
    ),
    paper_bgcolor=BG,
    plot_bgcolor=SURFACE,
    font=dict(family="monospace", color=TEXT),
    legend=dict(
        bgcolor="rgba(17,19,24,0.8)", bordercolor=BORDER, borderwidth=1,
        font=dict(color=SUBTEXT, size=10, family="monospace"),
        x=0.02, y=0.56,
    ),
    barmode="group",
    margin=dict(t=60, b=40, l=40, r=40),
    height=820,
    hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(family="monospace", color=TEXT)),
)

for axis in ["xaxis", "yaxis", "xaxis2", "yaxis2", "xaxis3", "yaxis3"]:
    fig.update_layout(**{axis: axis_style})

for text, x, y in [
    ("VIEWS & CLONES OVER TIME", 0.02, 0.82),
    ("CLONES BREAKDOWN",         0.02, 0.38),
    ("VIEWS VS CLONES",          0.70, 0.38),
]:
    fig.add_annotation(
        text=f"<span style='color:{SUBTEXT};font-size:10px;font-family:monospace;letter-spacing:0.12em'>{text}</span>",
        xref="paper", yref="paper", x=x, y=y,
        showarrow=False, align="left",
    )
#save
out = csv_path.parent / "traffic_dashboard.html"
fig.write_html(str(out), include_plotlyjs="cdn")
print(f"[✓] Saved interactive dashboard → {out}")

fig.show()