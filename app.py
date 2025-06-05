from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim

app = Flask(__name__)
signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


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

        if 'latitude' in data and 'longitude' in data:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        elif 'location' in data:
            latitude, longitude = get_lat_lon_from_location(data['location'])
        else:
            return jsonify({"error": "Location not provided"}), 400

        dt_utc = convert_jst_to_utc(year, month, day, hour, minute)
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60.0)

        swe.set_topo(longitude, latitude, 0)

        planets = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
            "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO, "MeanNode": swe.MEAN_NODE, "TrueNode": swe.TRUE_NODE
        }

        results, planet_houses, retrogrades = {}, {}, {}

        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')
        houses, cusp_signs = {}, {}
        for i in range(12):
            lon = cusps[i] % 360
            deg = lon % 30
            sign = signs[int(lon / 30)]
            houses[f"House{i+1}"] = round(lon, 2)
            cusp_signs[f"House{i+1}"] = f"{sign} {deg:.1f}°"

        angles = {"ASC": round(ascmc[0], 2), "MC": round(ascmc[1], 2)}
        cusp_list = list(cusps) + [cusps[0] + 360]

        for name, planet in planets.items():
            result, ret = swe.calc_ut(jd, planet)
            lon = result[0] % 360
            deg = lon % 30
            sign = signs[int(lon / 30)]
            results[name] = f"{sign} {deg:.1f}°"
            retrogrades[name] = result[3] < 0 if len(result) > 3 else False
            for i in range(12):
                if cusp_list[i] <= lon < cusp_list[i + 1]:
                    planet_houses[name] = f"House {i+1}"
                    break

        return jsonify({
            "input_datetime_utc": dt_utc.strftime("%Y-%m-%d %H:%M"),
            "latitude": latitude,
            "longitude": longitude,
            "planets": results,
            "planet_houses": planet_houses,
            "retrograde": retrogrades,
            "houses": cusp_signs,
            "angles": angles
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/transit', methods=['POST'])
def get_transit_positions():
    try:
        data = request.json
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])
        minute = int(data['minute'])

        dt_utc = convert_jst_to_utc(year, month, day, hour, minute)
        jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60.0)

        planets = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
            "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO, "MeanNode": swe.MEAN_NODE, "TrueNode": swe.TRUE_NODE
        }

        results, retrogrades = {}, {}
        for name, planet in planets.items():
            result, _ = swe.calc_ut(jd, planet)
            lon = result[0] % 360
            deg = round(lon % 30, 1)
            sign = signs[int(lon / 30)]
            results[name] = f"{sign} {deg}°"
            retrogrades[name] = result[3] < 0 if len(result) > 3 else False

        return jsonify({
            "input_datetime_utc": dt_utc.strftime("%Y-%m-%d %H:%M"),
            "planets": results,
            "retrograde": retrogrades
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/solararc', methods=['POST'])
def get_solar_arc_positions():
    try:
        data = request.json

        birth_year = int(data['birth_year'])
        birth_month = int(data['birth_month'])
        birth_day = int(data['birth_day'])
        birth_hour = int(data['birth_hour'])
        birth_minute = int(data['birth_minute'])

        target_year = int(data['target_year'])
        target_month = int(data['target_month'])
        target_day = int(data['target_day'])

        birth_dt = convert_jst_to_utc(birth_year, birth_month, birth_day, birth_hour, birth_minute)
        jd_birth = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day, birth_dt.hour + birth_dt.minute / 60.0)
        sun_birth, _ = swe.calc_ut(jd_birth, swe.SUN)

        target_dt = convert_jst_to_utc(target_year, target_month, target_day, birth_hour, birth_minute)
        jd_target = swe.julday(target_dt.year, target_dt.month, target_dt.day, target_dt.hour + target_dt.minute / 60.0)
        sun_target, _ = swe.calc_ut(jd_target, swe.SUN)

        arc = (sun_target[0] - sun_birth[0]) % 360

        planets = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
            "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO, "MeanNode": swe.MEAN_NODE, "TrueNode": swe.TRUE_NODE
        }

        results = {}
        for name, planet in planets.items():
            result, _ = swe.calc_ut(jd_birth, planet)
            lon = (result[0] + arc) % 360
            deg = round(lon % 30, 1)
            sign = signs[int(lon / 30)]
            results[name] = f"{sign} {deg}°"

        return jsonify({
            "solar_arc_degree": round(arc, 2),
            "planets": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
