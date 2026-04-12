"""
traffic visualizer — interactive dashboard for your traffic_log.csv
usage:
    python traffic_viz.py path/to/traffic_log.csv

requires: pip install plotly pandas
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# check deps before doing anything
try:
    import pandas as pd
except ImportError:
    print("pandas is required. Install it with: pip install pandas")
    sys.exit(1)

try:
    import plotly  # noqa: F401
except ImportError:
    print("plotly is required. Install it with: pip install plotly")
    sys.exit(1)

# ── Theme
PALETTE = [
    "#00e5a0", "#a78bfa", "#4f8cff", "#fb923c", "#22d3ee",
    "#fb7185", "#fbbf24", "#34d399", "#818cf8", "#f472b6",
    "#2dd4bf", "#c084fc", "#60a5fa", "#f97316", "#a3e635",
    "#e879f9", "#38bdf8", "#fdba74", "#86efac", "#d8b4fe",
]


def short_name(full_name):
    return full_name.split("/")[-1] if "/" in full_name else full_name


def get_color(i):
    return PALETTE[i % len(PALETTE)]


def build_dashboard_html(df, csv_path):
    """Build a fully self-contained HTML dashboard string."""

    df["date"] = df["timestamp_utc"].dt.strftime("%Y-%m-%d")
    repos = sorted(df["repo"].unique())

    # Pre-compute all data as JSON-serializable structures
    repo_data = {}
    for i, repo in enumerate(repos):
        rdf = df[df["repo"] == repo]

        views_daily = (
            rdf[rdf["type"] == "view"]
            .groupby("date", as_index=False)
            .agg(count=("count", "sum"), uniques=("uniques", "sum"))
            .sort_values("date")
        )
        clones_daily = (
            rdf[rdf["type"] == "clone"]
            .groupby("date", as_index=False)
            .agg(count=("count", "sum"), uniques=("uniques", "sum"))
            .sort_values("date")
        )

        repo_data[repo] = {
            "short": short_name(repo),
            "color": get_color(i),
            "views_total": int(rdf[rdf["type"] == "view"]["count"].sum()),
            "views_uniques": int(rdf[rdf["type"] == "view"]["uniques"].sum()),
            "clones_total": int(rdf[rdf["type"] == "clone"]["count"].sum()),
            "clones_uniques": int(rdf[rdf["type"] == "clone"]["uniques"].sum()),
            "views_dates": views_daily["date"].tolist(),
            "views_counts": views_daily["count"].tolist(),
            "views_unique_counts": views_daily["uniques"].tolist(),
            "clones_dates": clones_daily["date"].tolist(),
            "clones_counts": clones_daily["count"].tolist(),
            "clones_unique_counts": clones_daily["uniques"].tolist(),
        }

    date_range = f'{df["date"].min()} → {df["date"].max()}'
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Traffic Dashboard — {csv_path.stem}</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  :root {{
    --bg: #08090d;
    --surface: #0f1117;
    --surface-2: #161922;
    --border: #1e2030;
    --border-hover: #2a2e42;
    --green: #00e5a0;
    --green-dim: rgba(0,229,160,0.12);
    --purple: #a78bfa;
    --purple-dim: rgba(167,139,250,0.12);
    --blue: #4f8cff;
    --text: #e2e8f0;
    --text-secondary: #8892a4;
    --text-muted: #4a4f63;
    --radius: 12px;
  }}

  body {{
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}

  /* ── Header ── */
  .header {{
    padding: 20px 28px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
  }}
  .header-left {{
    display: flex;
    align-items: center;
    gap: 14px;
  }}
  .header h1 {{
    font-size: 18px;
    font-weight: 600;
    letter-spacing: -0.02em;
  }}
  .header h1 span {{
    color: var(--green);
  }}
  .header-badge {{
    font-size: 11px;
    color: var(--text-secondary);
    background: var(--surface-2);
    padding: 4px 10px;
    border-radius: 20px;
    border: 1px solid var(--border);
  }}
  .header-meta {{
    font-size: 11px;
    color: var(--text-muted);
  }}

  /* ── Layout ── */
  .layout {{
    display: flex;
    flex: 1;
    overflow: hidden;
  }}

  /* ── Sidebar ── */
  .sidebar {{
    width: 260px;
    min-width: 260px;
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    background: var(--surface);
    overflow: hidden;
  }}
  .sidebar-header {{
    padding: 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .sidebar-title {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-secondary);
  }}
  .sidebar-actions {{
    display: flex;
    gap: 6px;
  }}
  .sidebar-actions button {{
    flex: 1;
    padding: 6px 0;
    font-size: 10px;
    font-family: inherit;
    font-weight: 500;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--surface-2);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s;
  }}
  .sidebar-actions button:hover {{
    border-color: var(--border-hover);
    color: var(--text);
    background: var(--border);
  }}
  .sidebar-search {{
    width: 100%;
    padding: 8px 12px;
    font-size: 11px;
    font-family: inherit;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
    color: var(--text);
    outline: none;
    transition: border-color 0.15s;
  }}
  .sidebar-search::placeholder {{
    color: var(--text-muted);
  }}
  .sidebar-search:focus {{
    border-color: var(--green);
  }}
  .repo-list {{
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }}
  .repo-list::-webkit-scrollbar {{
    width: 4px;
  }}
  .repo-list::-webkit-scrollbar-track {{
    background: transparent;
  }}
  .repo-list::-webkit-scrollbar-thumb {{
    background: var(--border);
    border-radius: 4px;
  }}
  .repo-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.12s;
    user-select: none;
  }}
  .repo-item:hover {{
    background: var(--surface-2);
  }}
  .repo-item.hidden-by-search {{
    display: none;
  }}

  /* Custom checkbox */
  .repo-check {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid var(--border-hover);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
  }}
  .repo-item.checked .repo-check {{
    border-color: var(--color);
    background: var(--color);
  }}
  .repo-item.checked .repo-check::after {{
    content: '✓';
    font-size: 10px;
    color: var(--bg);
    font-weight: 700;
  }}

  .repo-color {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .repo-name {{
    font-size: 11px;
    color: var(--text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
  }}
  .repo-stat {{
    font-size: 10px;
    color: var(--text-muted);
    flex-shrink: 0;
  }}

  /* ── Main content ── */
  .main {{
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}

  /* ── Stat cards ── */
  .stats-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }}
  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .stat-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }}
  .stat-value {{
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.03em;
  }}
  .stat-value.green {{ color: var(--green); }}
  .stat-value.purple {{ color: var(--purple); }}
  .stat-value.blue {{ color: var(--blue); }}
  .stat-sub {{
    font-size: 10px;
    color: var(--text-muted);
  }}

  /* ── Chart panels ── */
  .chart-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}
  .chart-panel {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .chart-panel.full {{
    grid-column: 1 / -1;
  }}
  .chart-title {{
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-secondary);
    padding-left: 4px;
  }}
  .chart-container {{
    width: 100%;
  }}

  /* ── Tabs ── */
  .tab-bar {{
    display: flex;
    gap: 2px;
    background: var(--bg);
    border-radius: 8px;
    padding: 3px;
    width: fit-content;
  }}
  .tab-btn {{
    font-family: inherit;
    font-size: 11px;
    font-weight: 500;
    padding: 6px 14px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s;
  }}
  .tab-btn.active {{
    background: var(--surface-2);
    color: var(--text);
  }}
  .tab-btn:hover:not(.active) {{
    color: var(--text-secondary);
  }}

  /* ── Responsive ── */
  @media (max-width: 900px) {{
    .sidebar {{ width: 220px; min-width: 220px; }}
    .stats-row {{ grid-template-columns: repeat(2, 1fr); }}
    .chart-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1><span>traffic</span>.log</h1>
    <span class="header-badge">{len(repos)} repos</span>
    <span class="header-badge">{date_range}</span>
  </div>
  <div class="header-meta">Generated {generated_at}</div>
</div>

<div class="layout">
  <!-- Sidebar -->
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">Repositories</div>
      <input type="text" class="sidebar-search" id="repoSearch" placeholder="Search repos..." oninput="filterRepoList()">
      <div class="sidebar-actions">
        <button onclick="selectAll()">Select all</button>
        <button onclick="selectNone()">Deselect all</button>
        <button onclick="selectTop(5)">Top 5</button>
      </div>
    </div>
    <div class="repo-list" id="repoList"></div>
  </div>

  <!-- Main -->
  <div class="main">
    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-label">Total Views</span>
        <span class="stat-value green" id="statViews">0</span>
        <span class="stat-sub" id="statViewsSub">0 unique</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Total Clones</span>
        <span class="stat-value purple" id="statClones">0</span>
        <span class="stat-sub" id="statClonesSub">0 unique</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Active Repos</span>
        <span class="stat-value blue" id="statRepos">0</span>
        <span class="stat-sub" id="statReposSub">selected</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Date Range</span>
        <span class="stat-value" style="font-size:14px;color:var(--text-secondary)" id="statRange">{date_range}</span>
        <span class="stat-sub" id="statDays">&nbsp;</span>
      </div>
    </div>

    <div class="chart-panel full">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <span class="chart-title">Views Over Time</span>
        <div class="tab-bar">
          <button class="tab-btn active" onclick="setViewsMode('total',this)">Total</button>
          <button class="tab-btn" onclick="setViewsMode('unique',this)">Unique</button>
        </div>
      </div>
      <div class="chart-container" id="chartViews"></div>
    </div>

    <div class="chart-panel full">
      <div style="display:flex;align-items:center;justify-content:space-between">
        <span class="chart-title">Clones Over Time</span>
        <div class="tab-bar">
          <button class="tab-btn active" onclick="setClonesMode('total',this)">Total</button>
          <button class="tab-btn" onclick="setClonesMode('unique',this)">Unique</button>
        </div>
      </div>
      <div class="chart-container" id="chartClones"></div>
    </div>

    <div class="chart-grid">
      <div class="chart-panel">
        <span class="chart-title">Repo Comparison</span>
        <div class="chart-container" id="chartBar"></div>
      </div>
      <div class="chart-panel">
        <span class="chart-title">Views vs Clones</span>
        <div class="chart-container" id="chartDonut"></div>
      </div>
    </div>
  </div>
</div>

<script>
// ── Data ──
const REPO_DATA = {json.dumps(repo_data)};
const REPOS = {json.dumps(repos)};

// ── State ──
const selected = new Set(REPOS);
let viewsMode = 'total';
let clonesMode = 'total';

// ── Theme constants ──
const THEME = {{
  bg: '#08090d',
  surface: '#0f1117',
  border: '#1e2030',
  text: '#e2e8f0',
  muted: '#4a4f63',
  sub: '#8892a4',
  green: '#00e5a0',
  purple: '#a78bfa',
}};

const CHART_LAYOUT = {{
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: {{ family: "'JetBrains Mono', monospace", color: THEME.sub, size: 10 }},
  margin: {{ t: 10, b: 40, l: 50, r: 20 }},
  xaxis: {{
    gridcolor: THEME.border, gridwidth: 1,
    tickfont: {{ color: THEME.muted, size: 9 }},
    linecolor: THEME.border, zerolinecolor: THEME.border,
  }},
  yaxis: {{
    gridcolor: THEME.border, gridwidth: 1,
    tickfont: {{ color: THEME.muted, size: 9 }},
    linecolor: THEME.border, zerolinecolor: THEME.border,
  }},
  hoverlabel: {{
    bgcolor: THEME.surface,
    bordercolor: THEME.border,
    font: {{ family: "'JetBrains Mono', monospace", color: THEME.text, size: 11 }},
  }},
  showlegend: false,
}};

const PLOTLY_CONFIG = {{
  displayModeBar: false,
  responsive: true,
}};


// ── Sidebar ──

function buildSidebar() {{
  const list = document.getElementById('repoList');
  // Sort repos by total traffic (views+clones) descending
  const sorted = [...REPOS].sort((a, b) => {{
    const ta = REPO_DATA[a].views_total + REPO_DATA[a].clones_total;
    const tb = REPO_DATA[b].views_total + REPO_DATA[b].clones_total;
    return tb - ta;
  }});

  sorted.forEach(repo => {{
    const d = REPO_DATA[repo];
    const item = document.createElement('div');
    item.className = 'repo-item checked';
    item.dataset.repo = repo;
    item.style.setProperty('--color', d.color);
    item.innerHTML = `
      <div class="repo-check"></div>
      <div class="repo-color" style="background:${{d.color}}"></div>
      <span class="repo-name" title="${{repo}}">${{d.short}}</span>
      <span class="repo-stat">${{d.views_total + d.clones_total}}</span>
    `;
    item.addEventListener('click', () => toggleRepo(repo, item));
    list.appendChild(item);
  }});
}}

function toggleRepo(repo, el) {{
  if (selected.has(repo)) {{
    selected.delete(repo);
    el.classList.remove('checked');
  }} else {{
    selected.add(repo);
    el.classList.add('checked');
  }}
  updateAll();
}}

function selectAll() {{
  REPOS.forEach(r => selected.add(r));
  document.querySelectorAll('.repo-item').forEach(el => el.classList.add('checked'));
  updateAll();
}}

function selectNone() {{
  selected.clear();
  document.querySelectorAll('.repo-item').forEach(el => el.classList.remove('checked'));
  updateAll();
}}

function selectTop(n) {{
  selected.clear();
  const sorted = [...REPOS].sort((a, b) => {{
    const ta = REPO_DATA[a].views_total + REPO_DATA[a].clones_total;
    const tb = REPO_DATA[b].views_total + REPO_DATA[b].clones_total;
    return tb - ta;
  }});
  sorted.slice(0, n).forEach(r => selected.add(r));
  document.querySelectorAll('.repo-item').forEach(el => {{
    el.classList.toggle('checked', selected.has(el.dataset.repo));
  }});
  updateAll();
}}

function filterRepoList() {{
  const q = document.getElementById('repoSearch').value.toLowerCase();
  document.querySelectorAll('.repo-item').forEach(el => {{
    const repo = el.dataset.repo.toLowerCase();
    el.classList.toggle('hidden-by-search', q && !repo.includes(q));
  }});
}}


// ── Stats ──

function updateStats() {{
  let views = 0, viewsU = 0, clones = 0, clonesU = 0;
  selected.forEach(repo => {{
    const d = REPO_DATA[repo];
    views += d.views_total;
    viewsU += d.views_uniques;
    clones += d.clones_total;
    clonesU += d.clones_uniques;
  }});
  document.getElementById('statViews').textContent = views.toLocaleString();
  document.getElementById('statViewsSub').textContent = viewsU.toLocaleString() + ' unique';
  document.getElementById('statClones').textContent = clones.toLocaleString();
  document.getElementById('statClonesSub').textContent = clonesU.toLocaleString() + ' unique';
  document.getElementById('statRepos').textContent = selected.size;
  document.getElementById('statReposSub').textContent = `of ${{REPOS.length}} selected`;
}}


// ── Charts ──

function renderViews() {{
  const traces = [];
  selected.forEach(repo => {{
    const d = REPO_DATA[repo];
    const y = viewsMode === 'unique' ? d.views_unique_counts : d.views_counts;
    traces.push({{
      x: d.views_dates, y: y,
      name: d.short, mode: 'lines+markers',
      line: {{ color: d.color, width: 2 }},
      marker: {{ color: d.color, size: 4 }},
      hovertemplate: `<b>${{d.short}}</b><br>%{{x}}<br>${{viewsMode === 'unique' ? 'Unique' : 'Views'}}: %{{y}}<extra></extra>`,
    }});
  }});
  const layout = {{
    ...CHART_LAYOUT,
    height: 280,
    yaxis: {{ ...CHART_LAYOUT.yaxis, title: {{ text: viewsMode === 'unique' ? 'Unique Visitors' : 'Views', font: {{ color: THEME.muted, size: 10 }} }} }},
  }};
  Plotly.react('chartViews', traces, layout, PLOTLY_CONFIG);
}}

function renderClones() {{
  const traces = [];
  selected.forEach(repo => {{
    const d = REPO_DATA[repo];
    const y = clonesMode === 'unique' ? d.clones_unique_counts : d.clones_counts;
    traces.push({{
      x: d.clones_dates, y: y,
      name: d.short, mode: 'lines+markers',
      line: {{ color: d.color, width: 2 }},
      marker: {{ color: d.color, size: 4 }},
      hovertemplate: `<b>${{d.short}}</b><br>%{{x}}<br>${{clonesMode === 'unique' ? 'Unique' : 'Clones'}}: %{{y}}<extra></extra>`,
    }});
  }});
  const layout = {{
    ...CHART_LAYOUT,
    height: 260,
    yaxis: {{ ...CHART_LAYOUT.yaxis, title: {{ text: clonesMode === 'unique' ? 'Unique Cloners' : 'Clones', font: {{ color: THEME.muted, size: 10 }} }} }},
  }};
  Plotly.react('chartClones', traces, layout, PLOTLY_CONFIG);
}}

function renderBar() {{
  const repos = [...selected].sort((a, b) => {{
    const va = REPO_DATA[a].views_total || 0;
    const vb = REPO_DATA[b].views_total || 0;
    return vb - va;
  }});
  const names = repos.map(r => REPO_DATA[r].short);
  const viewsVals = repos.map(r => REPO_DATA[r].views_total || 0);
  const clonesVals = repos.map(r => REPO_DATA[r].clones_total || 0);

  // Compute adaptive margins so labels and outside text are not clipped
  const maxLabelChars = names.reduce((m, n) => Math.max(m, (n || '').length), 0);
  const leftMargin = Math.min(320, 60 + maxLabelChars * 7);
  const allVals = viewsVals.concat(clonesVals);
  const maxValLen = allVals.length ? Math.max(...allVals.map(v => String(v).length)) : 1;
  const rightMargin = Math.min(160, 30 + maxValLen * 10);

  const traces = [
    {{
      y: names, x: viewsVals, text: viewsVals.map(v => v.toLocaleString()),
      textposition: 'outside', textfont: {{ color: THEME.text, size: 10 }},
      name: 'Views', type: 'bar', orientation: 'h',
      marker: {{ color: THEME.green, opacity: 0.85 }},
      hovertemplate: '<b>%{{y}}</b><br>Views: %{{text}}<extra></extra>',
      cliponaxis: false,
    }},
    {{
      y: names, x: clonesVals, text: clonesVals.map(v => v.toLocaleString()),
      textposition: 'outside', textfont: {{ color: THEME.text, size: 10 }},
      name: 'Clones', type: 'bar', orientation: 'h',
      marker: {{ color: THEME.purple, opacity: 0.85 }},
      hovertemplate: '<b>%{{y}}</b><br>Clones: %{{text}}<extra></extra>',
      cliponaxis: false,
    }},
  ];
  const h = Math.max(200, repos.length * 28 + 60);
  const layout = {{
    ...CHART_LAYOUT,
    height: h,
    barmode: 'group',
    showlegend: true,
    legend: {{
      font: {{ color: THEME.sub, size: 10 }},
      bgcolor: 'transparent',
      orientation: 'h', x: 0, y: 1.12,
    }},
    yaxis: {{
      ...CHART_LAYOUT.yaxis,
      automargin: true,
      autorange: 'reversed',
      tickfont: {{ color: THEME.sub, size: 10, family: "'JetBrains Mono', monospace" }},
    }},
    xaxis: {{
      ...CHART_LAYOUT.xaxis,
      type: 'linear',
      tickformat: ',',
      title: {{ text: 'Count', font: {{ color: THEME.muted, size: 10 }} }},
    }},
    margin: {{ t: 30, b: 40, l: leftMargin, r: rightMargin }},
  }};
  Plotly.react('chartBar', traces, layout, PLOTLY_CONFIG);
}}

function renderDonut() {{
  let views = 0, clones = 0;
  selected.forEach(repo => {{
    views += REPO_DATA[repo].views_total;
    clones += REPO_DATA[repo].clones_total;
  }});
  const traces = [{{
    labels: ['Views', 'Clones'],
    values: [views, clones],
    type: 'pie',
    // slightly smaller hole so percent labels fit inside the ring
    hole: 0.55,
    // show percent labels inside the donut for clarity
    textinfo: 'percent',
    textposition: 'inside',
    insidetextfont: {{ color: THEME.text, family: "'JetBrains Mono', monospace", size: 13 }},
    marker: {{
      colors: [THEME.green, THEME.purple],
      line: {{ color: THEME.bg, width: 3 }},
    }},
    textfont: {{ color: THEME.text, family: "'JetBrains Mono', monospace", size: 12 }},
    hovertemplate: '<b>%{{label}}</b><br>%{{value:,}} (%{{percent}})<extra></extra>',
  }}];
  const layout = {{
    ...CHART_LAYOUT,
    height: Math.max(200, [...selected].length * 28 + 60),
    margin: {{ t: 10, b: 10, l: 10, r: 10 }},
    annotations: [{{
      text: `<b>${{(views + clones).toLocaleString()}}</b><br><span style="font-size:10px;color:${{THEME.muted}}">total</span>`,
      showarrow: false,
      font: {{ size: 20, color: THEME.text, family: "'JetBrains Mono', monospace" }},
    }}],
  }};
  Plotly.react('chartDonut', traces, layout, PLOTLY_CONFIG);
}}


// ── Tab handlers ──

function setViewsMode(mode, btn) {{
  viewsMode = mode;
  btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderViews();
}}

function setClonesMode(mode, btn) {{
  clonesMode = mode;
  btn.parentElement.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderClones();
}}


// ── Update everything ──

function updateAll() {{
  updateStats();
  renderViews();
  renderClones();
  renderBar();
  renderDonut();
}}


// ── Init ──
buildSidebar();
updateAll();
</script>

</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="GitHub Traffic Dashboard")
    parser.add_argument("csv", nargs="?", default="traffic_log.csv", help="Path to traffic_log.csv")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[!] File not found: {csv_path}")
        print("    Usage: python traffic_viz.py path/to/traffic_log.csv")
        sys.exit(1)

    df = pd.read_csv(csv_path, parse_dates=["timestamp_utc", "captured_at_utc"])
    print(f"[✓] Loaded {len(df)} rows from {csv_path}")

    if "repo" not in df.columns:
        print("[i] Old CSV format (no 'repo' column) — treating as single repo")
        df["repo"] = "unknown"

    repos = sorted(df["repo"].unique())
    print(f"[i] Repos: {', '.join(repos)}")

    html = build_dashboard_html(df, csv_path)

    out = csv_path.parent / "traffic_dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"[✓] Saved dashboard → {out}")

    # Try to open in browser
    import webbrowser
    webbrowser.open(str(out.resolve()))


if __name__ == "__main__":
    main()