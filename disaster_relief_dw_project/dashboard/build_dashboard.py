"""
Rebuilds dashboard.html from dashboard_template.html + the latest dashboard_data.json.
Run this AFTER export_dashboard_data.py, any time the database has changed and you
want the dashboard to reflect it.
"""
import json

with open("dashboard_data.json") as f:
    data = json.load(f)

with open("dashboard_template.html") as f:
    html = f.read()

html = html.replace("__DATA_JSON__", json.dumps(data))

with open("dashboard.html", "w") as f:
    f.write(html)

print("dashboard.html rebuilt from latest data.")
