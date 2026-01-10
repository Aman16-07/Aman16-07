#!/usr/bin/env python3
"""
Generate GitHub contribution SVG charts.
Fetches contribution data from GitHub and creates light/dark themed SVGs.
"""

import os
import json
import requests
from datetime import datetime, timedelta

GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'Antxnrx')

def fetch_contributions():
    """Fetch contribution data from GitHub's GraphQL API via the contribution calendar."""
    # Use GitHub's contribution calendar endpoint
    url = f"https://github.com/users/{GITHUB_USERNAME}/contributions"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
        
        # Parse contribution counts from the HTML
        contributions = parse_contribution_html(html)
        return contributions
    except Exception as e:
        print(f"Error fetching contributions: {e}")
        return get_sample_data()

def parse_contribution_html(html):
    """Parse contribution data from GitHub's contribution page HTML."""
    from datetime import datetime, timedelta
    
    contributions = []
    today = datetime.now()
    
    # Look for data-count attributes in the HTML
    import re
    
    # Find all contribution data
    pattern = r'data-date="([^"]+)"[^>]*data-count="(\d+)"'
    matches = re.findall(pattern, html)
    
    if not matches:
        # Alternative pattern
        pattern = r'data-count="(\d+)"[^>]*data-date="([^"]+)"'
        matches = re.findall(pattern, html)
        matches = [(date, count) for count, date in matches]
    
    if matches:
        # Get last 28 days
        date_counts = {date: int(count) for date, count in matches}
        
        for i in range(28):
            date = (today - timedelta(days=27-i)).strftime('%Y-%m-%d')
            contributions.append(date_counts.get(date, 0))
    else:
        contributions = get_sample_data()
    
    return contributions

def get_sample_data():
    """Return sample data if fetching fails."""
    import random
    random.seed(42)
    return [random.randint(0, 15) for _ in range(28)]

def calculate_stats(contributions):
    """Calculate statistics from contribution data."""
    total = sum(contributions)
    avg_per_day = round(total / len(contributions), 1) if contributions else 0
    best_day = max(contributions) if contributions else 0
    this_week = sum(contributions[-7:]) if len(contributions) >= 7 else sum(contributions)
    
    return {
        'total': total,
        'avg_per_day': avg_per_day,
        'best_day': best_day,
        'this_week': this_week
    }

def generate_chart_path(contributions, chart_height=160):
    """Generate SVG path data for the contribution chart."""
    if not contributions:
        return "", ""
    
    max_val = max(contributions) if max(contributions) > 0 else 1
    width = 800
    points = len(contributions)
    
    # Calculate x positions
    x_positions = [i * (width / (points - 1)) for i in range(points)]
    
    # Calculate y positions (inverted because SVG y-axis goes down)
    y_positions = [chart_height - (c / max_val * (chart_height - 20)) if max_val > 0 else chart_height for c in contributions]
    
    # Generate smooth curve using line segments
    path_points = list(zip(x_positions, y_positions))
    
    # Create line path
    line_path = f"M {path_points[0][0]} {path_points[0][1]}"
    for x, y in path_points[1:]:
        line_path += f" L {x} {y}"
    
    # Create fill path
    fill_path = line_path + f" L {width} {chart_height} L 0 {chart_height} Z"
    
    # Generate circle points
    circles = [(x, y) for x, y in path_points]
    
    return line_path, fill_path, circles

def generate_svg(contributions, stats, theme='light'):
    """Generate an SVG chart with the given theme."""
    
    if theme == 'light':
        bg_color = '#ffffff'
        text_color = '#1d1d1f'
        subtitle_color = '#86868b'
        accent_color = '#007AFF'
        label_color = '#6e6e73'
        grid_color = '#f5f5f7'
        point_stroke = '#ffffff'
    else:
        bg_color = '#1c1c1e'
        text_color = '#ffffff'
        subtitle_color = '#98989d'
        accent_color = '#0a84ff'
        label_color = '#98989d'
        grid_color = '#2c2c2e'
        point_stroke = '#1c1c1e'
    
    line_path, fill_path, circles = generate_chart_path(contributions)
    
    # Generate circle elements
    circle_elements = ""
    for x, y in circles[::2]:  # Every other point to avoid clutter
        circle_elements += f'  <circle cx="{x}" cy="{y}" r="4" fill="{accent_color}" stroke="{point_stroke}" stroke-width="2"/>\n'
    
    # Best day marker
    max_idx = contributions.index(max(contributions)) if contributions else 0
    max_x = max_idx * (800 / (len(contributions) - 1)) if len(contributions) > 1 else 0
    max_val = max(contributions) if contributions else 1
    max_y = 160 - (max(contributions) / max_val * 140) if max_val > 0 else 160
    
    today = datetime.now().strftime('%b %d, %Y')
    
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="400" viewBox="0 0 900 400">
<style>
  * {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; }}
  .title {{ font-size: 26px; font-weight: 700; fill: {text_color}; }}
  .subtitle {{ font-size: 15px; font-weight: 500; fill: {subtitle_color}; }}
  .stat-value {{ font-size: 36px; font-weight: 700; fill: {accent_color}; }}
  .stat-label {{ font-size: 12px; font-weight: 600; fill: {label_color}; text-transform: uppercase; }}
  .axis-label {{ font-size: 11px; fill: {subtitle_color}; font-weight: 500; }}
  .grid-line {{ stroke: {grid_color}; stroke-width: 1; stroke-dasharray: 4, 4; }}
  .chart-line {{ fill: none; stroke: {accent_color}; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
  .chart-fill {{ fill: {accent_color}; opacity: 0.15; }}
  .tooltip-bg {{ fill: {text_color}; opacity: 0.9; }}
  .tooltip-text {{ fill: {bg_color}; font-size: 11px; font-weight: 600; }}
</style>

<!-- Background -->
<rect width="900" height="400" fill="{bg_color}" rx="20"/>

<!-- Header -->
<text class="title" x="40" y="45">GitHub Contributions</text>
<text class="subtitle" x="40" y="68">@{GITHUB_USERNAME} • Last 4 weeks • Updated {today}</text>

<!-- Stats -->
<g transform="translate(40, 100)">
  <text class="stat-value" x="0" y="28">{stats['total']}</text>
  <text class="stat-label" x="0" y="48">Total</text>
  
  <text class="stat-value" x="180" y="28">{stats['avg_per_day']}</text>
  <text class="stat-label" x="180" y="48">Avg/Day</text>
  
  <text class="stat-value" x="360" y="28">{stats['best_day']}</text>
  <text class="stat-label" x="360" y="48">Best Day</text>
  
  <text class="stat-value" x="540" y="28">{stats['this_week']}</text>
  <text class="stat-label" x="540" y="48">This Week</text>
</g>

<!-- Chart -->
<g transform="translate(60, 180)">
  <!-- Grid lines -->
  <line class="grid-line" x1="0" y1="0" x2="800" y2="0"/>
  <line class="grid-line" x1="0" y1="40" x2="800" y2="40"/>
  <line class="grid-line" x1="0" y1="80" x2="800" y2="80"/>
  <line class="grid-line" x1="0" y1="120" x2="800" y2="120"/>
  <line class="grid-line" x1="0" y1="160" x2="800" y2="160"/>
  
  <!-- Y-axis labels -->
  <text class="axis-label" x="-10" y="5" text-anchor="end">{stats['best_day']}</text>
  <text class="axis-label" x="-10" y="85" text-anchor="end">{stats['best_day']//2}</text>
  <text class="axis-label" x="-10" y="165" text-anchor="end">0</text>
  
  <!-- Area fill -->
  <path class="chart-fill" d="{fill_path}"/>
  
  <!-- Line -->
  <path class="chart-line" d="{line_path}"/>
  
  <!-- Data points -->
{circle_elements}
  
  <!-- X-axis labels -->
  <text class="axis-label" x="0" y="180" text-anchor="middle">Week 1</text>
  <text class="axis-label" x="200" y="180" text-anchor="middle">Week 2</text>
  <text class="axis-label" x="400" y="180" text-anchor="middle">Week 3</text>
  <text class="axis-label" x="600" y="180" text-anchor="middle">Week 4</text>
  <text class="axis-label" x="800" y="180" text-anchor="middle">Today</text>
  
  <!-- Best day tooltip -->
  <g transform="translate({max_x}, {max_y})">
    <rect class="tooltip-bg" x="-30" y="-24" width="60" height="20" rx="4"/>
    <text class="tooltip-text" x="0" y="-10" text-anchor="middle">{stats['best_day']} best</text>
  </g>
</g>

</svg>'''
    
    return svg

def main():
    print(f"Fetching contributions for {GITHUB_USERNAME}...")
    contributions = fetch_contributions()
    
    print(f"Got {len(contributions)} days of data")
    print(f"Contributions: {contributions}")
    
    stats = calculate_stats(contributions)
    print(f"Stats: {stats}")
    
    # Generate light theme
    light_svg = generate_svg(contributions, stats, 'light')
    with open('svg/contributions-light.svg', 'w') as f:
        f.write(light_svg)
    print("Generated svg/contributions-light.svg")
    
    # Generate dark theme
    dark_svg = generate_svg(contributions, stats, 'dark')
    with open('svg/contributions-dark.svg', 'w') as f:
        f.write(dark_svg)
    print("Generated svg/contributions-dark.svg")

if __name__ == '__main__':
    main()
