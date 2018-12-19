#!/usr/bin/env python3

import geocoder
import pandas as pd

wk_dir = "C:\\cygwin64\\home\\mohammed.akbar\\git_files\\snippets\\geocoding\\"
input_file = wk_dir + 'sample_addresses.xlsx'
output_file = wk_dir + 'geocoded_results.xlsx'

feed = pd.read_excel(input_file, encoding='utf8')
feed['addrs'] = feed['address'] + " " + feed['pincode'].map(str)


def find_map_coordinates(known_address):
    """
    Function to find latitude and longtitude for the address.
    Input
    :full_address: input string with full address (like "building number, street name, pincode, Country")
    :geolocator: geocoder object

    Output
    :latitude, longitude, accuracy, valid_address: values of latitude and longtitude for the input address
    """
    try:
        location = geocoder.bing(known_address, key = 'AsbHXxf7M04WU4ckmJujP0-ZoB5t0qnlxKttB4IA72YIEbC0eXP-pxOvlgsA-Esa')
        return location.lat, location.lng, location.confidence, location.address
    except IndexError:
        return 0

location = feed.apply(lambda row: find_map_coordinates(row['addrs']),axis=1).tolist()
results = pd.DataFrame(location,columns = ['latitude', 'longitude', 'accuracy', 'valid_address'])

results_file = pd.concat([feed,results],axis=1)

writer = pd.ExcelWriter(wk_dir + 'output.xlsx')
results_file.to_excel(writer,'sheet1')
writer.save()
