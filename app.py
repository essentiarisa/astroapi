from flask import Flask, request, jsonify
import swisseph as swe
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return 'Astrology API is running!'

@app.route('/get_planets', methods=['POST'])
def get_planets():
    data = request.json
    birthdate = data.get("birthdate")
    time = data.get("time")
    lon = float(data.get("lon"))
    lat = float(data.get("lat"))

    dt = datetime.datetime.strptime(f"{birthdate} {time}", "%Y-%m-%d %H:%M")
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)

    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN
    }

    result = {}
    for name, code in planets.items():
        pos, _ = swe.calc_ut(jd, code)
        result[name] = round(pos[0], 2)

    return jsonify(result)
