import pandas as pd
import geopandas as gpd
import os


def process_rent_file(base_dir):
    """Process .xls file and convert to readable data"""

    print('Processing London rental data...')
    raw_filepath = os.path.join(base_dir, 'data', 'raw', 'ons_london_rental_2023_data.xls')

    raw_rental_df = pd.read_excel(raw_filepath, sheet_name=5, header=None)
    cols = raw_rental_df.iloc[2].to_list()
    rental_df = raw_rental_df.iloc[3:1977]
    rental_df.columns = cols

    # clean data
    rental_df = rental_df.rename(columns={'Postcode District': 'OUTCODE',
                                            'Bedroom Category': 'ROOM_TYPE',
                                            'Count of rents': 'RENT_COUNT',
                                            'Mean': 'MEAN_RENT',
                                            'Lower quartile': 'LQ_RENT',
                                            'Median': 'MEDIAN_RENT',
                                            'Upper quartile': 'UQ_RENT'})
    pd.set_option('future.no_silent_downcasting', True)
    rental_df = rental_df.replace({'.':0, '..':0, '-':0})
    rental_df.insert(2, 'NO_ROOMS', rental_df['ROOM_TYPE'].map({'Room':1, 'One Bedroom':1, 'Studio':1, 'Two Bedrooms':2, 'Three Bedrooms':3, 'Four or More Bedrooms':4}).astype('int'))
    rental_df.loc[:,['RENT_COUNT','MEAN_RENT','LQ_RENT','MEDIAN_RENT','UQ_RENT' ]] = rental_df[['RENT_COUNT','MEAN_RENT','LQ_RENT','MEDIAN_RENT','UQ_RENT' ]].astype('int32')

    raw_borough_df = pd.read_excel(raw_filepath, sheet_name=4, header=None)
    borough_df = raw_borough_df.iloc[3:201].drop(columns=[1,2,3,4,5,6]).drop_duplicates()

    processed_filepath = os.path.join(base_dir, 'data', 'processed')
    try:
        rental_df.to_csv(os.path.join(processed_filepath, 'ons_london_rental_2023_data.csv'), index=None)
        borough_df.to_csv(os.path.join(processed_filepath, 'borough_names.csv'), index=None, header=False) # make borough names .csv
        print('Successfully processed London rental data')
        return borough_df
    except Exception as e:
        print('Error: ', e)


def separate_ENG_from_LSOA_lookup(base_dir):
    uk_lookup_filepath = os.path.join(os.path.join(base_dir, 'data', 'raw'), 'postcode_LSOA_lookup.csv')
    dtypes = {0:'str', 1:'str', 2:'str', 3:'float64', 4:'float64', 5:'float64', 6:'str', 7:'str', 8:'str', 9:'str', 10:'str', 11:'str', 12:'str', 13:'str'}
    uk_lookup_df = pd.read_csv(uk_lookup_filepath, encoding='latin1', dtype=dtypes)

    eng_lookup_df = uk_lookup_df[['pcds','lsoa21nm']].dropna()
    eng_lookup_df.columns = [col.upper() for col in eng_lookup_df.columns]
    eng_lookup_df['OUTCODE'] = eng_lookup_df['PCDS'].str[:-4]
    eng_lookup_df = eng_lookup_df.drop(columns='PCDS')

    # try:
    #     eng_lookup_df.to_csv(os.path.join(base_dir, 'data', 'processed', 'eng_outcode_LSOA_lookup.csv'), index=False)
    # except Exception as e:
    #     print('Error: ', e)
    
    return eng_lookup_df


def process_LSOA_files(base_dir, boroughs_df, eng_lookup_df):
    print('Processing all files from UK LSOA shapefile...')

    shp_folder_filepath = os.path.join(base_dir, 'data', 'raw', 'uk_LSOA_shapefile')

    # extract london only geometries
    boroughs = boroughs_df[0].to_list()
    uk_outline = gpd.read_file(str(os.path.join(shp_folder_filepath, 'LSOA_2021_EW_BFE_V10.shp'))) # read uk shp file
    ldn_lsoa_outline = uk_outline[uk_outline['LSOA21NM'].str.contains('|'.join(boroughs), case=False)].drop(columns='LSOA21NMW') # separate london only geometries
    ldn_lsoa_outline.insert(1, 'BOROUGH', ldn_lsoa_outline.loc[:,'LSOA21NM'].str[:-5]) # create borough column
    ldn_lsoa_outline.loc[:,'geometry']=ldn_lsoa_outline.loc[:,'geometry'].to_crs('EPSG:4326') # convert to crs
    ldn_borough_outline = ldn_lsoa_outline[['BOROUGH', 'geometry']].dissolve(by='BOROUGH').reset_index() # combine geometries by borough
    ldn_borough_outline.insert(0, 'LAT', ldn_borough_outline['geometry'].centroid.y) # find new centroid and separate lat and lon
    ldn_borough_outline.insert(1, 'LONG', ldn_borough_outline['geometry'].centroid.x)

    # lookup LSOA and match to outcodes
    merged_df = pd.merge(ldn_lsoa_outline, eng_lookup_df, on='LSOA21NM', how='inner').drop_duplicates(subset=['LSOA21NM']).reset_index(drop=True)
    merged_df['LON'] = merged_df.geometry.centroid.x
    merged_df['LAT'] = merged_df.geometry.centroid.y
    ldn_lsoa_outline = merged_df[['LSOA21CD', 'OUTCODE', 'BOROUGH', 'LON', 'LAT', 'geometry']]

    # separate OUTCODE geometries
    ldn_outcode_outline = ldn_lsoa_outline[['BOROUGH', 'OUTCODE', 'geometry']].dissolve(by='OUTCODE')
    ldn_outcode_outline = ldn_outcode_outline.reset_index()
    ldn_outcode_outline['LON'] = ldn_outcode_outline.geometry.centroid.x
    ldn_outcode_outline['LAT'] = ldn_outcode_outline.geometry.centroid.y
    ldn_outcode_outline = ldn_outcode_outline[['OUTCODE', 'BOROUGH', 'LON', 'LAT', 'geometry']]


    # write out dfs to geojsons
    try:
        ldn_lsoa_outline.to_file(
            os.path.join(base_dir, 'data', 'processed', 'ldn_LSOA_outline.geojson'), 
            driver='GeoJSON'
        )
        ldn_outcode_outline.to_file(
            os.path.join(base_dir, 'data', 'processed', 'ldn_outcode_outline.geojson'), 
            driver='GeoJSON'
        )
        ldn_borough_outline.to_file(
            os.path.join(base_dir, 'data', 'processed', 'ldn_borough_outline.geojson'), 
            driver='GeoJSON'
        )
        print('Successfully processed all files from UK LSOA shapefile')
    except Exception as e:
        print('Error: ', e)

    return ldn_lsoa_outline['LSOA21CD'].tolist()


def process_house_prices_data(base_dir, ldn_lsoa_codes, eng_lookup_df):
    """Process .xls file and convert to readable data"""

    print('Processing house prices data...')
    raw_filepath = os.path.join(base_dir, 'data', 'raw', 'ons_house_prices_data.xls')

    raw_rental_df = pd.read_excel(raw_filepath, sheet_name=5, header=None)
    df = raw_rental_df.iloc[6:34759, 2:114]
    cols = raw_rental_df.iloc[5, 2:114].tolist()
    df.columns = cols
    df = df.rename(columns={'LSOA name':'LSOA21NM', 'LSOA code':'LSOA21CD'})
    df = df[df.LSOA21CD.isin(ldn_lsoa_codes)]
    house_prices_df = pd.merge(df, eng_lookup_df, on='LSOA21NM', how='inner').drop_duplicates(subset=['LSOA21NM']).reset_index(drop=True)
    house_prices_df.insert(1, 'BOROUGH', house_prices_df.loc[:,'LSOA21NM'].str[:-5]) # create borough column
    house_prices_df = house_prices_df.drop(columns='LSOA21NM').reset_index(drop=True)
    house_prices_df = house_prices_df.replace({':':0})
    house_prices_df[house_prices_df.columns[house_prices_df.columns.str.contains('Year')]].astype('float')
    for col in house_prices_df.columns[house_prices_df.columns.str.contains('Year')]:
        year = col[-4:]
        house_prices_df = house_prices_df.rename(columns={col:year})
    house_prices_df = house_prices_df.loc[:, ~house_prices_df.columns.duplicated()]

    processed_filepath = os.path.join(base_dir, 'data', 'processed')
    try:
        house_prices_df.to_csv(os.path.join(processed_filepath, 'ons_house_prices_data.csv'), index=None)
        print('Successfully processed house prices data')
    except Exception as e:
        print('Error: ', e)


def process_age_sex_data(base_dir, ldn_lsoa_codes, eng_lookup_df):
    """Process .xls file and convert to readable data"""

    print('Processing age and sex data...')
    raw_filepath = raw_filepath = os.path.join(base_dir, 'data', 'raw', 'ons_age_sex_data_2022.xlsx')
    
    raw_age_sex_df = pd.read_excel(raw_filepath, sheet_name=5, header=None)
    cols = raw_age_sex_df.iloc[3].tolist()
    raw_age_sex_df.columns=cols
    df = raw_age_sex_df.iloc[4:35676].drop(columns=['LAD 2021 Code','LAD 2021 Name'])    
    df = df.rename(columns={'LSOA 2021 Name':'LSOA21NM', 'LSOA 2021 Code':'LSOA21CD'})
    df = df[df.LSOA21CD.isin(ldn_lsoa_codes)]
    age_sex_df = pd.merge(df, eng_lookup_df, on='LSOA21NM', how='inner').drop_duplicates(subset=['LSOA21NM']).reset_index(drop=True)
    age_sex_df.insert(1, 'BOROUGH', age_sex_df.loc[:,'LSOA21NM'].str[:-5]) # create borough column
    age_sex_df = age_sex_df.drop(columns='LSOA21NM').reset_index(drop=True)

    processed_filepath = os.path.join(base_dir, 'data', 'processed')
    try:
        age_sex_df.to_csv(os.path.join(processed_filepath, 'ons_age_sex_data_2022.csv'), index=None)
        print('Successfully processed age and sex data')
    except Exception as e:
        print('Error: ', e)





if __name__ == '__main__':
    base_dir = os.getcwd()
    eng_lookup_df = separate_ENG_from_LSOA_lookup(base_dir)
    boroughs_df = process_rent_file(base_dir)
    ldn_lsoa_codes = process_LSOA_files(base_dir, boroughs_df, eng_lookup_df)
    process_house_prices_data(base_dir, ldn_lsoa_codes, eng_lookup_df)
    process_age_sex_data(base_dir, ldn_lsoa_codes, eng_lookup_df)