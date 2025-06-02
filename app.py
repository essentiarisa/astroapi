from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim

app = Flask(__name__)
signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def convert_jst_to_utc(year, month, day, hour, minute):
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = datetime(year, month, day, hour, minute, tzinfo=jst)
    dt_utc = dt_jst.astimezone(pytz.utc)
    return dt_utc

def get_lat_lon_from_location(location_name):
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

        # Location handling
        if 'latitude' in data and 'longitude' in data:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        elif 'location' in data:
            latitude, longitude = get_lat_lon_from_location(data['location'])
        else:
            return jsonify({"error": "Location not provided"}), 400

        dt_utc = convert_jst_to_utc(year, month, day, hour, minute)
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60.0)

        # Set topocentric position
        swe.set_topo(longitude, latitude, 0)

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
        planet_houses = {}
        planet_motion = {}

        # ハウス計算（Porphyry方式）
        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')
        cusp_list = list(cusps) + [cusps[0] + 360]  # for wrapping
        houses = {}
        for i, cusp in enumerate(cusps):
            sign_index = int(cusp % 360 / 30)
            deg = round(cusp % 30, 1)
            houses[f"House{i+1}"] = f"{signs[sign_index]} {deg}°"

        angles = {
            "ASC": round(ascmc[0], 2),
            "MC": round(ascmc[1], 2)
        }

        for name, planet in planets.items():
            position, speed = swe.calc_ut(jd, planet, swe.FLG_SPEED)
            lon = round(position[0], 2)
            deg = round(lon % 30, 1)
            sign_index = int(lon / 30)
            sign = signs[sign_index]
            retrograde = "R" if speed[0] < 0 else "D"
            results[name] = f"{sign} {deg}°"
            planet_motion[name] = retrograde

            for i in range(12):
                if cusp_list[i] <= lon < cusp_list[i+1]:
                    planet_houses[name] = f"House {i+1}"
                    break

        return jsonify({
            "input_datetime_utc": dt_utc.strftime("%Y-%m-%d %H:%M"),
            "latitude": latitude,
            "longitude": longitude,
            "planets": results,
            "planet_motion": planet_motion,
            "planet_houses": planet_houses,
            "houses": houses,
            "angles": angles
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
