import requests
import geopandas as pd
import numpy as np
import datetime
import time
from tqdm import tqdm
import os


# find journey time from every outcode to the city of London
def download_commute_data_tfl(base_dir):
    ldn_outcode_filepath = os.path.join(base_dir, 'data', 'processed', 'ldn_outcode_outline.geojson')
    
    # get coordinates of all stations
    ldn_outcode_outline = pd.read_file(ldn_outcode_filepath)
    lat,lon = ldn_outcode_outline.LAT, ldn_outcode_outline.LON
    all_coords = np.column_stack((lat, lon))

    # get today's date to collect data on (except if it is a weekend, choose a weekday date)
    if datetime.date.today().weekday()>4:
        date = (datetime.date.today() + datetime.timedelta(days=2)).strftime('%Y%m%d')
    else:
        date = datetime.date.today().strftime('%Y%m%d')

    print('Downloading commute data from TfL API...')
    print('Takes approximately 15 minutes')
    durations = []
    start_time = time.time()
    for i, coords in enumerate(tqdm(all_coords)):
        start = f'{coords[0]},{coords[1]}'
        end = '51.515815,-0.064799' # city of london coords

        if start == end:
            durations.append(0)
        else:
            url = f'https://api.tfl.gov.uk/Journey/JourneyResults/{start}/to/{end}'

            #params
            params={'date': date,
                    'time':'0845',
                    'timeIs':'Arriving',
                    'journeyPreference':'LeastTime',
                    'nationalSearch': 'false'}
            
            try:
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                        
                data = response.json()
                durations.append(data['journeys'][0]['duration'])
            except Exception as e:
                durations.append(0)
            
            time.sleep(0.5)
            end_time = time.time()

            # check if 50 requests per minute has been reached (rate limit):
            if (i + 1) % 50 == 0 and i > 0:
                if end_time-start_time < 60:
                    time.sleep(61-(end_time-start_time))
                start_time = time.time()
        
    ldn_outcode_outline['JOURNEY_TIME'] = durations

    try:
        ldn_outcode_outline.to_file(
            os.path.join(base_dir, 'data', 'processed', 'ldn_outcode_outline.geojson'), 
            driver='GeoJSON')
    except Exception as e:
        print('Error: ', e)


if __name__ == '__main__':
    base_dir = os.getcwd()
    download_commute_data_tfl(base_dir)