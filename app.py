from flask import Flask, request, jsonify
from datetime import datetime
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

app = Flask(__name__)
signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def convert_to_utc(year,month,day,hour,minute,lat,lon):
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat,lng=lon)
    local_dt = pytz.timezone(tz_name).localize(datetime(year,month,day,hour,minute),is_dst=None)
    return local_dt.astimezone(pytz.utc)

def get_lat_lon_from_location(name):
    loc = Nominatim(user_agent="astro_app").geocode(name)
    if loc: return loc.latitude, loc.longitude
    raise ValueError("Location not found")

@app.route('/planet',methods=['POST'])
def get_planet_positions():
    try:
        data = request.json
        year,month,day,hour,minute = [int(data[k]) for k in ['year','month','day','hour','minute']]
        if 'latitude' in data and 'longitude' in data:
            lat,lon = float(data['latitude']),float(data['longitude'])
        else:
            lat,lon = get_lat_lon_from_location(data['location'])
        dt = convert_to_utc(year,month,day,hour,minute,lat,lon)
        jd = swe.julday(dt.year,dt.month,dt.day,dt.hour+dt.minute/60)
        swe.set_topo(lon,lat,0)

        planets = {"Sun":swe.SUN,"Moon":swe.MOON,"Mercury":swe.MERCURY,
                   "Venus":swe.VENUS,"Mars":swe.MARS,"Jupiter":swe.JUPITER,
                   "Saturn":swe.SATURN,"Uranus":swe.URANUS,"Neptune":swe.NEPTUNE,
                   "Pluto":swe.PLUTO,"MeanNode":swe.MEAN_NODE,"TrueNode":swe.TRUE_NODE}

        cusps,ascmc = swe.houses(jd,lat,lon,b'P')
        cusp_list = list(cusps)+[cusps[0]+360]

        results,planet_houses,retro = {},{},{}
        cusp_signs = {f"House{i+1}": f"{signs[int((cusps[i]%360)/30)]} {round((cusps[i]%30),1)}°" for i in range(12)}
        angles = {"ASC":round(ascmc[0],2),"MC":round(ascmc[1],2)}

        for name,pl in planets.items():
            result, flags = swe.calc_ut(jd, pl)
            lon_deg = result[0] % 360
            speed_long = result[3]
            sign = signs[int(lon_deg / 30)]
            results[name] = f"{sign} {round(lon_deg % 30, 1)}°"
            retro[name] = speed_long < 0

            for i in range(12):
                if cusp_list[i] <= lon_deg < cusp_list[i+1]:
                    planet_houses[name] = f"House {i+1}"
                    break

        return jsonify({
            "input_datetime_utc": dt.strftime("%Y-%m-%d %H:%M"),
            "latitude": lat,"longitude": lon,
            "planets": results,"planet_houses":planet_houses,
            "retrograde":retro,"houses":cusp_signs,"angles":angles
        })
    except Exception as e:
        return jsonify({"error":str(e)}),400

if __name__=='__main__':
    app.run(debug=True)
