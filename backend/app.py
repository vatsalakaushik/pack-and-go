# backend/app.py
print(">>> app.py starting")

from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import requests
import os
from urllib.parse import quote_plus


app = Flask(__name__, static_folder="../frontend", static_url_path="/")

CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "city_trends.csv")
if os.path.exists(CSV_PATH):
    try:
        trends_df = pd.read_csv(CSV_PATH).fillna("")
    except Exception as e:
        print("Error reading CSV:", e)
        trends_df = None
else:
    print("CSV not found at", CSV_PATH)
    trends_df = None

def get_trend_for_city(city):
    if trends_df is None:
        return None
    try:
        row = trends_df[trends_df["city"].str.lower() == city.lower()]
        if row.empty:
            return None
        d = row.iloc[0].to_dict()
        for k in ["top_categories","top_colors","top_items"]:
            if k in d and isinstance(d[k], str):
                d[k] = [x.strip() for x in d[k].split(";") if x.strip()]
            else:
                d[k] = []
        return d
    except Exception as e:
        print("Error in get_trend_for_city:", e)
        return None

def fetch_weather(city):
    key = os.environ.get("OWM_API_KEY")
    if not key:
        return {"error": "OWM_API_KEY not set"}

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": key, "units": "metric"}

    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            # if error, "no data" message
            return {"error": "no live weather data available for this city right now"}

        j = r.json()
        weather = {
            "temp_c": j.get("main", {}).get("temp"),
            "feels_like_c": j.get("main", {}).get("feels_like"),
            "humidity": j.get("main", {}).get("humidity"),
            "description": j.get("weather", [{}])[0].get("description"),
            "main": j.get("weather", [{}])[0].get("main", ""),
            "wind_m_s": j.get("wind", {}).get("speed"),
        }
        weather["is_rain"] = ("rain" in j) or (weather["main"].lower() in ["rain", "drizzle", "thunderstorm"])
        return weather

    except Exception:
        # same behavior on exceptions
        return {"error": "no live weather data available for this city right now"}


@app.route("/api/pack", methods=["POST"])
def api_pack():
    data = request.get_json() or {}
    city = data.get("city") or data.get("location")
    if not city:
        return jsonify({"error":"city required"}), 400

    trend = get_trend_for_city(city)
    weather = fetch_weather(city)

    # simple packing rules
    packing = []
    if isinstance(weather, dict) and weather.get("temp_c") is not None:
        t = weather["temp_c"]
        if t <= 5:
            packing += ["heavy coat", "thermal layers", "gloves", "warm hat", "scarf"]
        elif t <= 15:
            packing += ["jacket", "sweater", "long pants"]
        elif t <= 22:
            packing += ["light jacket", "cardigan", "jeans"]
        else:
            packing += ["t-shirts", "shorts", "sunhat"]

    else:
        packing += ["comfortable clothes"]

    if isinstance(weather, dict) and weather.get("is_rain"):
        packing += ["umbrella", "waterproof jacket"]

    if trend and trend.get("top_items"):
        packing += [it for it in trend["top_items"][:6]]

    # essentials
    packing += ["underwear", "socks", "toothbrush", "phone charger"]

    # dedupe preserving order
    seen = set(); final = []
    for p in packing:
        if p not in seen:
            final.append(p); seen.add(p)

    return jsonify({
        "city": city,
        "trend": trend,
        "weather": weather,
        "packing_list": final
    })

@app.route("/api/dashboard-url")
def dashboard_url():
    """
    Return the Tableau Public embed URL based on the selected view/tab,
    and filter by City if provided.
    """
    view = request.args.get("view", "popular")  
    city = (request.args.get("city", "") or "").strip()

    base_map = {
        "popular": "https://public.tableau.com/views/ColorTrends/ColorTrends?:embed=yes&:showVizHome=no",
        "seasonal": "https://public.tableau.com/views/SeasonalPreferences_17636448129230/SeasonalPreferences?:embed=yes&:showVizHome=no",
        "gender":   "https://public.tableau.com/views/CityGenderDivision/CityGenderDivision?:embed=yes&:showVizHome=no",
        "styles":   "https://public.tableau.com/views/ClothingTrends_17636449862130/ClothingTrends?:embed=yes&:showVizHome=no",
    }

    base = base_map.get(view)
    if not base:
        return jsonify({"embed_url": ""})

    # If user typed a city, append Tableau's City filter.
    # Field name is exact
    if city:
        # URL-encode:
        base = f"{base}&City={quote_plus(city)}"

    return jsonify({"embed_url": base})



# serve frontend static files
@app.route("/", defaults={"path":""})
@app.route("/<path:path>")
def serve_static(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
