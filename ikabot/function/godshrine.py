from ikabot.helpers.botComm import *
from ikabot.helpers.getJson import getCity
from ikabot.helpers.pedirInfo import getIdsOfCities
import traceback
import re

from ikabot.helpers.process import set_child_mode
from ikabot.helpers.varios import wait


def shrine(session):
    """
    Parameters
    ----------
    session : ikabot.web.session.Session

    Returns
    -------
    commercial_cities : list[dict]
    """
    cities_ids = getIdsOfCities(session)[0]
    shrine_info = {'grace_periods': {}, 'favor_amount': None}
    for city_id in cities_ids:
        html = session.get(city_url + city_id)
        city = getCity(html)
        for pos, building in enumerate(city['position']):
            if building['building'] == 'shrineOfOlympus':
                city['pos'] = pos
                result = getshrineHtml(session, city)
                jsondata = result['json_data']
                data = jsondata[2][1]
                data1 = jsondata[1][1][1]
                match = re.search(r'<span id="currentFavor">(\d+)</span>', data1)
                shrine_info['favor_amount'] = int(match.group(1)) # the value of favor

                for key, value in data.items():
                    if '.gracePeriod' in key:
                        parts = key.split('.')
                        if len(parts) > 2 and parts[1].startswith('god_'):
                            god_name = parts[1].split('_')[1]
                            shrine_info['grace_periods'][god_name] = value

                # Print the grace periods for each god
                return shrine_info




def getshrineHtml(session, city):
    """
    Parameters
    ----------
    session : ikabot.web.session.Session
    city : dict
    """
    url = 'view=shrineOfOlympus&cityId={}&position={:d}&currentCityId={}&backgroundView=city&actionRequest={}&ajax=1'.format(city['id'], city['pos'], city['id'], actionRequest)
    data = session.post(url)
    json_data = json.loads(data, strict=False)
    return {'url': url, 'json_data': json_data}

def checkGracePeriods(session):
    """
    Check the grace periods of the gods and return those below 7 hours.
    """
    shrine_info = shrine(session)
    grace_periods = shrine_info['grace_periods']
    alert_gods = {}
    for god, period in grace_periods.items():
        # Extract days and hours from the period string
        matches = re.findall(r'(\d+)D\s+(\d+)h', period)
        if matches:
            days, hours = map(int, matches[0])
            total_minutes = days * 24 * 60 + hours * 60
        else:
            # Handle cases where only hours are present
            matches = re.findall(r'(\d+)h', period)
            if matches:
                hours = int(matches[0])
                total_minutes = hours * 60
            else:
                # If no match, skip this god
                continue

        if total_minutes < 180:  # 3 hours in minutes
            alert_gods[god] = period

    return alert_gods

def do_it_shrine(session, event, stdin_fd, predetermined_input):
    sys.stdin = os.fdopen(stdin_fd)
    config.predetermined_input = predetermined_input

    cities_ids = getIdsOfCities(session)[0]
    for city_id in cities_ids:
        html = session.get(city_url + city_id)
        city = getCity(html)
        for pos, building in enumerate(city['position']):
            if building['building'] == 'shrineOfOlympus':
                city['pos'] = pos
                result = getshrineHtml(session, city)
                url = result['url']

    try:
        set_child_mode(session)
        event.set()

        while True:
            gods_to_alert = checkGracePeriods(session)
            for god, period in gods_to_alert.items():
                # Check if the favor amount is sufficient
                shrine_info = shrine(session)
                if shrine_info['favor_amount'] < 100:
                    # Not enough favor, send alert to Telegram
                    msg = f"ALERT: Not enough favor to donate for {god}. Grace period is below 7 hours: {period}"
                    sendToBot(session, msg)
                else:
                    god_ids = {'pan ': 1, 'dionysus ': 2, 'tyche ': 3, 'plutus ': 4, 'theia ': 5, 'hephaistos ': 6}
                    if god in god_ids:
                        donate_url = f"action=DonateFavorToGod&godId={god_ids[god.lower()]}&{url}"
                        session.post(donate_url)


            wait(60 * 60)  # Wait for an hour before checking again
    except KeyboardInterrupt:
        event.set()
        return
    except Exception as e:
        msg = f'Error in do_it_shrine: {traceback.format_exc()}'
        sendToBot(session, msg)
    finally:
        session.logout()
