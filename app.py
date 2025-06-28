from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

app = Flask(__name__)
signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def convert_to_utc(year,month,day,hour,minute,lat,lon):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat,lng=lon)
    local_dt = pytz.timezone(tz_name).localize(datetime(year,month,day,hour,minute),is_dst=None)
    return local_dt.astimezone(pytz.utc)

def get_lat_lon_from_location(name):
    loc = Nominatim(user_agent="astro_app").geocode(name)
    if loc: return loc.latitude, loc.longitude
    raise ValueError("Location not found")

# /solararcルート（年齢×1度法）
@app.route('/solararc', methods=['POST'])
def get_solar_arc_positions():
    try:
        data = request.json
        birth_year, birth_month, birth_day = int(data['birth_year']), int(data['birth_month']), int(data['birth_day'])
        birth_hour, birth_minute = int(data['birth_hour']), int(data['birth_minute'])

        if 'latitude' in data and 'longitude' in data:
            lat, lon = float(data['latitude']), float(data['longitude'])
        else:
            lat, lon = get_lat_lon_from_location(data['location'])

        now = datetime.now(pytz.timezone('Asia/Tokyo'))

        age = now.year - birth_year - ((now.month, now.day) < (birth_month, birth_day))
        solar_arc = (age * 1.0) % 360

        natal_utc = convert_to_utc(birth_year, birth_month, birth_day, birth_hour, birth_minute, lat, lon)
        natal_jd = swe.julday(natal_utc.year, natal_utc.month, natal_utc.day, natal_utc.hour + natal_utc.minute / 60)

        planets = {"Sun":swe.SUN,"Moon":swe.MOON,"Mercury":swe.MERCURY,"Venus":swe.VENUS,"Mars":swe.MARS,
                   "Jupiter":swe.JUPITER,"Saturn":swe.SATURN,"Uranus":swe.URANUS,"Neptune":swe.NEPTUNE,
                   "Pluto":swe.PLUTO,"MeanNode":swe.MEAN_NODE,"TrueNode":swe.TRUE_NODE}

        results = {}
        for name, pl in planets.items():
            natal_pos = swe.calc_ut(natal_jd, pl)[0][0] % 360
            progressed = (natal_pos + solar_arc) % 360
            sign = signs[int(progressed / 30)]
            results[name] = f"{sign} {round(progressed % 30, 1)}°"

        return jsonify({
            "solar_arc_datetime_utc": now.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M"),
            "latitude": lat,
            "longitude": lon,
            "solar_arc_degrees": round(solar_arc, 2),
            "planets": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__=='__main__':
    app.run(debug=True)
