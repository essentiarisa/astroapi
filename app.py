from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim

app = Flask(__name__)

signs = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# JST to UTC
def convert_jst_to_utc(year, month, day, hour, minute):
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = datetime(year, month, day, hour, minute, tzinfo=jst)
    return dt_jst.astimezone(pytz.utc)

# Location resolution
def get_lat_lon_from_location(location_name):
    geolocator = Nominatim(user_agent="astro_app")
    location = geolocator.geocode(location_name)
    if location:
        return location.latitude, location.longitude
    raise ValueError("Location not found")

# Degree to Zodiac format
def deg_to_sign(degree):
    sign_index = int(degree // 30)
    deg_in_sign = round(degree % 30, 1)
    return f"{signs[sign_index]} {deg_in_sign}°"

@app.route('/planet', methods=['POST'])
def get_planet_positions():
    data = request.json
    try:
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])
        minute = int(data['minute'])

        # Location resolution
        if 'latitude' in data and 'longitude' in data:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        elif 'location' in data:
            latitude, longitude = get_lat_lon_from_location(data['location'])
        else:
            return jsonify({"error": "Location not provided"}), 400

        dt_utc = convert_jst_to_utc(year, month, day, hour, minute)
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                        dt_utc.hour + dt_utc.minute / 60.0)

        swe.set_topo(longitude, latitude, 0)

        planets = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
            "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO, "MeanNode": swe.MEAN_NODE, "TrueNode": swe.TRUE_NODE
        }

        planet_results = {}
        planet_houses = {}
        retro_flags = {}

        # ハウス計算（Porphyry）
        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')
        cusp_list = list(cusps) + [cusps[0] + 360]

        house_cusps = {}
        for i in range(12):
            house_cusps[f"House{i+1}"] = deg_to_sign(cusps[i])

        angles = {
            "ASC": deg_to_sign(ascmc[0]),
            "MC": deg_to_sign(ascmc[1])
        }

        for name, planet in planets.items():
            pos_data = swe.calc_ut(jd, planet)
            lon = pos_data[0]
            speed = pos_data[3] if len(pos_data) > 3 else 0
            planet_results[name] = deg_to_sign(round(lon, 2))
            retro_flags[name] = speed < 0

            for i in range(12):
                if cusp_list[i] <= lon < cusp_list[i+1]:
                    planet_houses[name] = f"House {i+1}"
                    break

        return jsonify({
            "input_datetime_utc": dt_utc.strftime("%Y-%m-%d %H:%M"),
            "latitude": latitude,
            "longitude": longitude,
            "planets": planet_results,
            "retrograde_flags": retro_flags,
            "planet_houses": planet_houses,
            "house_cusps": house_cusps,
            "angles": angles
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
