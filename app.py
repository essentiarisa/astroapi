from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim

app = Flask(__name__)

# 日本時間（JST）→ UTC に変換
def convert_jst_to_utc(year, month, day, hour, minute):
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = datetime(year, month, day, hour, minute, tzinfo=jst)
    dt_utc = dt_jst.astimezone(pytz.utc)
    return dt_utc

# 場所名から緯度・経度を取得
def get_lat_lon(location_name):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(location_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError("場所が見つかりませんでした")

@app.route('/planet', methods=['POST'])
def get_planet_positions():
    data = request.json
    try:
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])
        minute = int(data['minute'])
        location_name = data.get('location', 'Tokyo')  # デフォルト東京

        # 時刻変換
        dt_utc = convert_jst_to_utc(year, month, day, hour, minute)
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                        dt_utc.hour + dt_utc.minute / 60.0)

        # 緯度・経度取得しtopo設定
        lat, lon = get_lat_lon(location_name)
        swe.set_topo(lon, lat, 0)

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
            "Pluto": swe.PLUTO
        }

        results = {}
        for name, planet in planets.items():
            pos, _ = swe.calc_ut(jd, planet)
            results[name] = round(pos[0], 2)

        return jsonify({
            "input_datetime_utc": dt_utc.strftime("%Y-%m-%d %H:%M"),
            "location": location_name,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "planets": results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
