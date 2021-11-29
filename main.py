import re
import datetime
import holidays
from flask import Flask, make_response, request, jsonify

regex = re.compile(re.escape("(Observed)"), re.IGNORECASE)

app = Flask("Holidays API")


def get_current_year():
    now = datetime.datetime.now()
    date = now.date()
    year = date.strftime("%Y")
    return year


def get_country_holidays(country: str, year: int):
    try:
        all_holidays = holidays.CountryHoliday(country=country, years=year, expand=True).items()
        clean_holidays = []
        for date, name in sorted(all_holidays):
            names = str(regex.sub("", name)).split("[")
            default_name = names[0]
            alt_name = None
            if len(names) > 1:
                alt_name = names[1]
                alt_name = alt_name[:-1].strip()
            print(default_name, alt_name)
            clean_holidays.append({
                "date": date.isoformat(),
                "name": default_name.strip(),
                "altName": alt_name
            })
        return clean_holidays
    except Exception as e:
        print(e)
        return []


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/holidays', methods=['GET'])
def get_holidays():
    country = request.args.get('country', default='', type=str)
    year = request.args.get('year', default=get_current_year(), type=int)
    print(country, year)
    if len(country) <= 0:
        return make_response(jsonify(error="No country or country code provided"), 400)
    country_holidays = get_country_holidays(country, year)
    if len(country_holidays) <= 0:
        error = "No holidays found for country or country code: \"" + country + "\""
        return make_response(jsonify(error=error), 404)
    return make_response(jsonify(holidays=country_holidays, count=len(country_holidays)), 200)


if __name__ == "__main__":
    # hoster = socket.gethostbyname(socket.gethostname())
    # app.run(host=hoster)
    app.run()
