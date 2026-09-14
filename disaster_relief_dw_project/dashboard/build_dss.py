import json

with open("dss_data.json") as f:
    data = json.load(f)

with open("dss_template.html") as f:
    html = f.read()

html = html.replace("__DATA_JSON__", json.dumps(data))

with open("dss.html", "w") as f:
    f.write(html)

print("dss.html built from latest data.")
