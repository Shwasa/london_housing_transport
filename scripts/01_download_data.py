import pandas as pd
import geopandas as gpd
import os
import requests
import zipfile
import time

def create_folders():
    """Create folders for datasets"""
    base_dir = os.getcwd()
    folders = [os.path.join('data', 'raw'),
               os.path.join('data', 'processed')]

    for folder in folders:
        full_filepath = os.path.join(base_dir, folder)
        if not os.path.exists(full_filepath):
            os.makedirs(full_filepath, exist_ok=True)
    
    print('Folders created')



#load data
def download_all_stations(base_dir):
    """Download all stations and their details"""

    stations=[]
    for transport in ['tube', 'elizabeth-line', 'dlr', 'overground', 'tram']:
        url = 'https://api.tfl.gov.uk/StopPoint/Mode/' + transport
        print('Downloading', ' '.join(transport.split('-')).title(), 'stations data...')
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            data = response.json()

            for stop in data['stopPoints']:
                try:
                    # collect specified transport stations only
                    if transport in stop['modes']:
                        station_data = {
                            'NAME': stop['commonName'],
                            'TYPE': ' '.join(transport.split('-')).title(),
                            'LAT': stop['lat'],
                            'LON': stop['lon'],
                            'ID': stop['id']
                        }
                        stations.append(station_data)
                except:
                    continue
        except Exception as e:
            print('Error: ', e)
    df = pd.DataFrame(stations)

    # remove all duplicates
    df = df.drop_duplicates(subset='ID', keep='first')
    tube_stations = df[df.TYPE=='Tube']
    tram_stations = df[df.TYPE=='Tram']
    elz_stations = df[df.TYPE=='Elizabeth Line']
    dlr_stations = df[df.TYPE=='Dlr']
    ovg_stations = df[df.TYPE=='Overground']

    tube_stations = tube_stations[tube_stations.NAME.str.contains('Underground Station')].drop_duplicates(subset='NAME')
    elz_stations = elz_stations[elz_stations.NAME.str.contains('Station')].drop_duplicates(subset='NAME')
    dlr_stations = dlr_stations[dlr_stations.NAME.str.contains('DLR Station')].drop_duplicates(subset='NAME')
    ovg_stations = ovg_stations[ovg_stations.NAME.str.contains('Rail Station')].drop_duplicates(subset='NAME')
    tram_stations = tram_stations[tram_stations.NAME.str.contains('Tram Stop')].drop_duplicates(subset='NAME')

    df = pd.concat([tube_stations, elz_stations, dlr_stations, ovg_stations, tram_stations], ignore_index=True)

    filename = 'transport_station_data.csv'
    filepath = os.path.join(base_dir, 'data', 'raw', filename)
    try:
        df.to_csv(filepath, index=False)
        print('Successfully downloaded all station data')
    except Exception as e:
        print('Error: ', e)



def download_rent_data(base_dir):
    """Download average rent data per outcode"""

    print('Downloading London rental data...')
    url = 'https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/adhocs/2052privaterentalmarketinlondonapril2023tomarch2024/londonrentalstatsaccessibleq12024.xlsx'

    try:
        response = requests.get(url)
        response.raise_for_status()

        filename = 'ons_london_rental_2023_data.xls'
        raw_filepath = os.path.join(base_dir, 'data', 'raw', filename)
        with open(raw_filepath, 'wb') as f:
            f.write(response.content)
            print('Successfully downloaded London rental data')
    except Exception as e:
            print('Error: ', e)


def extract_file(response, zip_filepath, destination_filepath):
    # write response into file
    with open(zip_filepath, 'wb') as f:
        f.write(response.content)

    # wait till file is loaded to disk
    while not (os.path.exists(zip_filepath) and os.path.getsize(zip_filepath) > 0):
        time.sleep(0.1)
    
    # extract all files from lookup .zip file
    print('Extracting files from zip folder...')
    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(destination_filepath)
        zip_ref.close()
        print('Successfully extracted file from zip folder')
    except Exception as e:
        print('Error: ', e)
        return

    # remove original .zip file
    try:
        os.remove(zip_filepath)
    except Exception as e:
        print('Error: ', e)
        return
    

def download_extract_uk_LSOA_data(base_dir):
    """Download UK LSOA zip file and extract all shapefiles"""

    print('Downloading UK LSOA outlines...')
    url = 'https://open-geography-portalx-ons.hub.arcgis.com/api/download/v1/items/b8263c2364e9452483a0e5783c6fdb53/shapefile?layers=0'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        zip_filepath = os.path.join(base_dir, 'data', 'raw', 'uk_LSOA_shapefile.zip')  
        shp_folder_filepath = os.path.join(base_dir, 'data', 'raw', 'uk_LSOA_shapefile')

        extract_file(response, zip_filepath, shp_folder_filepath)
        print('Successfully downloaded UK LSOA outlines')
    except Exception as e:
        print('Error: ', e)



def download_extract_uk_LSOA_lookup_data(base_dir):
    """Download and extract UK LSOA lookup file"""

    print('Downloading outcode-LSOA lookup...')
    url = 'https://www.arcgis.com/sharing/rest/content/items/589ae01495bf4ddfaaa25b96476d53d7/data'
    try:
        response = requests.get(url)
        response.raise_for_status()
        zip_filepath = os.path.join(base_dir, 'data', 'raw', 'uk_LSOA_lookup.zip')  
        
        # extract files
        dest_filepath = os.path.join(base_dir, 'data', 'raw')
        extract_file(response, zip_filepath, dest_filepath)
        print('Successfully downloaded outcode-LSOA lookup')

        uk_lookup_filepath = os.path.join(dest_filepath, 'postcode_LSOA_lookup.csv')
        os.rename(os.path.join(dest_filepath, 'PCD_OA21_LSOA21_MSOA21_LAD_MAY24_UK_LU.csv'), uk_lookup_filepath)
    except Exception as e:
        print('Error: ', e)

    

def download_house_prices_data(base_dir):
    """Download and extract house prices data"""

    print('Downloading house prices data...')
    url = 'https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/housing/datasets/medianpricepaidbylowerlayersuperoutputareahpssadataset46/current/hpssadataset46medianpricepaidforresidentialpropertiesbylsoa.zip'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        zip_filepath = os.path.join(base_dir, 'data', 'raw', 'ons_house_prices.zip')

        # extract files
        dest_filepath = os.path.join(base_dir, 'data', 'raw')
        extract_file(response, zip_filepath, dest_filepath)
        print('Successfully downloaded house prices data')

        house_prices_filepath = os.path.join(dest_filepath, 'ons_house_prices_data.xls')
        os.rename(os.path.join(dest_filepath, 'HPSSA Dataset 46 - Median price paid for residential properties by LSOA.xls'), house_prices_filepath)
    except Exception as e :
        print('Error: ', e)


def download_age_sex_data(base_dir):
    """Download and extract age and sex data"""

    print('Downloading age and sex data...')
    url = 'https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimates/mid2021andmid2022/sapelsoasyoatablefinal.xlsx'

    try:
        response = requests.get(url)
        response.raise_for_status()

        filename = 'ons_age_sex_data_2022.xlsx'
        raw_filepath = os.path.join(base_dir, 'data', 'raw', filename)
        with open(raw_filepath, 'wb') as f:
            f.write(response.content)
            print('Successfully downloaded age and sex data')
    except Exception as e:
            print('Error: ', e)




if __name__ == '__main__':
    base_dir = os.getcwd()
    create_folders()
    download_all_stations(base_dir)
    download_rent_data(base_dir)
    download_extract_uk_LSOA_data(base_dir)
    download_extract_uk_LSOA_lookup_data(base_dir)
    download_house_prices_data(base_dir)
    download_age_sex_data(base_dir)
