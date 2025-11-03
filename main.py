import re
import datetime
import holidays
import pycountry
import traceback
from flask import Flask, make_response, request, jsonify

regex = re.compile(re.escape("(Observed)"), re.IGNORECASE)

app = Flask("Holidays API")

countries = list(pycountry.countries)
countries_dict = {country.alpha_2: country for country in countries}


def get_current_year():
    now = datetime.datetime.now()
    date = now.date()
    year = date.strftime("%Y")
    return int(year)


def remove_spaces(string):
    return string.replace(" ", "")


def remove_duplicated_holidays(holidays_list: list, country: str):
    new_dict = dict()
    for day in holidays_list:
        holiday_name = day['name']
        new_dict[holiday_name] = []
    new_array = []
    for holiday_name in list(new_dict.keys()):
        holiday_options = [d for d in holidays_list if d['name'] == holiday_name]
        if len(holiday_options) == 1:
            new_array.append(holiday_options[0])
        else:
            try:
                observed_option = [d for d in holiday_options if d['observed']][0]
                not_observed_option = [d for d in holiday_options if not d['observed']][0]
                if country == "MX":
                    if holiday_name == "Año Nuevo" or holiday_name == "Día de la Independencia":
                        new_array.append(not_observed_option)
                    else:
                        new_array.append(observed_option)
                else:
                    new_array.append(observed_option)
            except Exception as e:
                print(e)
                # print(holiday_options)
                traceback.print_exc()
    return new_array


def get_country_holidays(country: str, year: int = None, upcoming: bool = False):
    try:
        supported = holidays.list_localized_countries()
        supported_langs = supported.get(remove_spaces(country))
        alt_langs = [item for item in supported_langs if
                     item != "en_US" and country != "US"] if supported_langs is not None else []
        all_holidays = holidays.country_holidays(country=remove_spaces(country), years=year, language="en_US").items()
        localized_holidays = []
        if len(alt_langs) > 0:
            all_localized_holidays = holidays.country_holidays(country=remove_spaces(country), years=year,
                                                               language=alt_langs[0]).items()
            if all_localized_holidays is not None:
                localized_holidays = list(sorted(all_localized_holidays))
        # Get the current date
        current_date = datetime.date.today()
        clean_holidays = []
        for index, (date, name) in enumerate(sorted(all_holidays)):
            if upcoming and date < current_date:
                continue
            clean_name = name.split(";")[0]
            names = str(regex.sub("", clean_name)).strip().split("[")
            default_name = names[0].strip()
            if len(localized_holidays) > 0:
                d, localized_name = localized_holidays[index]
                clean_localized_name_strings = localized_name.split(';')
                clean_name = clean_localized_name_strings[0].split('(')[0].strip()
            clean_holidays.append({
                "date": date.isoformat(),
                "name": clean_name.split('(')[0].strip(),
                "altName": default_name.split('(')[0].strip(),
                "originalName": " ".join(
                    [clean_name, f"[{default_name}]" if clean_name != default_name else "",
                     "(Observed)" if "observed" in name.lower() else ""]).strip(),
                "observed": "observed" in name.lower(),
            })
        return remove_duplicated_holidays(clean_holidays, country)
    except Exception as e:
        print(e)
        traceback.print_exc()
        return []


def get_supported_countries():
    try:
        supported_countries_and_subdivisions = holidays.list_supported_countries(True)
        supported_countries = []
        for country_code in supported_countries_and_subdivisions:
            supported_countries.append(country_code)
        return supported_countries
    except Exception as e:
        print(e)
        return []


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/holidays', methods=['GET'])
def get_holidays():
    country = str(request.args.get('country', default='', type=str)).upper()
    year = request.args.get('year', default=get_current_year(), type=int)
    upcoming = request.args.get('upcoming', default="false", type=str).lower() == "true"
    if len(country) <= 0:
        return make_response(jsonify(error="No country or country code provided"), 400)
    country_holidays = get_country_holidays(country, year, upcoming)
    if len(country_holidays) <= 0:
        error = "No holidays found for country or country code: \"" + country + "\". Try with ISO code. This code is case-sensitive"
        return make_response(jsonify(error=error), 404)
    try:
        country_obj = countries_dict["GB" if country == "UK" else country]
        country_data = {
            'name': country_obj.name,
            'officialName': country_obj.official_name if hasattr(country, 'official_name') else None,
            'flag': country_obj.flag,
            'alpha2': country_obj.alpha_2,
        }
        return make_response(
            jsonify(holidays=country_holidays, count=len(country_holidays), country=country_data), 200)
    except Exception as e:
        print(e)
        error = "No holidays found for country or country code: \"" + country + "\". Try with ISO code. This code is case-sensitive"
        return make_response(jsonify(error=error), 404)


@app.route('/countries', methods=['GET'])
def get_countries():
    supported_countries = get_supported_countries()
    if len(supported_countries) <= 0:
        return make_response(jsonify(error="No countries supported"), 404)
    countries_data = [
        {
            'alpha2': country.alpha_2,
            'flag': country.flag,
            'name': country.name,
            'officialName': country.official_name if hasattr(country, 'official_name') else None,
        }
        for code in supported_countries if (country := countries_dict.get(code)) is not None
    ]
    return make_response(
        jsonify(
            countries=sorted(supported_countries),
            count=len(supported_countries),
            countriesData={country['alpha2']: country for country in countries_data}),
        200)


if __name__ == "__main__":
    # hoster = socket.gethostbyname(socket.gethostname())
    # app.run(host=hoster)
    app.run()
