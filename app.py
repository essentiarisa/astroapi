from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim

app = Flask(__name__)
swe.set_ephe_path('.')  # Ephemerisファイルのパス（必要に応じて設定）

def convert_jst_to_utc(year, month, day, hour, minute):
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = datetime(year, month, day, hour, minute, tzinfo=jst)
    dt_utc = dt_jst.astimezone(pytz.utc)
    return dt_utc

def get_coordinates_from_location(location_name):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(location_name)
    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError("Location not found")

@app.route('/planet', methods=['POST'])
def get_planet_positions():
    data = request.json
    try:
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])
        minute = int(data['minute'])

        # 日本時間 → UTC
        dt_utc = convert_jst_to_utc(year, month, day, hour, minute)

        # 緯度経度を取得
        if 'latitude' in data and 'longitude' in data:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        elif 'location' in data:
            latitude, longitude = get_coordinates_from_location(data['location'])
        else:
            return jsonify({"error": "Location information is missing"}), 400

        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                        dt_utc.hour + dt_utc.minute / 60.0)

        planets = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mercury": swe.MERCURY,
            "Venus": swe.VENUS,
            "Mars": swe.MARS,
            "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN,
            "Uranus": swe.URANUS,
            "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO,
            "MeanNode": swe.MEAN_NODE,
            "TrueNode": swe.TRUE_NODE
        }

        results = {}
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

        for name, planet in planets.items():
            lon, _ = swe.calc_ut(jd, planet)
            degree = int(lon % 30)
            sign_index = int(lon / 30)
            results[name] = f"{signs[sign_index]} {degree}°"

        # ハウス計算（Porphyry方式）
        hsys = 'P'
        ascmc, cusps = swe.houses(jd, latitude, longitude, hsys)
        house_data = {f"House{i+1}": round(deg, 2) for i, deg in enumerate(cusps)}
        house_data.update({
            "ASC": round(ascmc[0], 2),
            "MC": round(ascmc[1], 2)
        })

        return jsonify({
            "input_datetime_utc": dt_utc.strftime("%Y-%m-%d %H:%M"),
            "latitude": latitude,
            "longitude": longitude,
            "planets": results,
            "houses": house_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
