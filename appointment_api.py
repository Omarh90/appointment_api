import os
import numpy as np
import pandas as pd
import requests
import json
from collections import Counter
from datetime import datetime

# TODO: - Get clarification on collision behavior for same-time appointments
#       - Precise integration testing for Main function

mappingfilename = "mapping.csv"  # zip_code to location_id mapping file

def ziptolocation(zip_code, file=mappingfilename, reverse = False):
    """

     convert zipcode to location ID using location table as key
     
     input: zipcode (int): zipcode of location (if reverse == False)
            zipcode (str): location_id of location (if reverse== True)
            file (os.path) directory of mapping key table
            reverse (bool): look up zipcode based on location_id
    
     output:  location ids as array of str (if reverse== False)
              zipcode if reverse==True 
    """
    # import zip to location mapping
    if 'mapping_df' not in dir():
        mapping_df = pd.read_csv(file)

    if not reverse:
        # Get location ID(s) from zipcode (in mapping.csv)
        location_ids = mapping_df[mapping_df.zip_code==zip_code].location_id
        output = location_ids.values
    else:
        # retrieve zipcode from location id
        location_id = zip_code # less confusing variable name
        zip_code = mapping_df[mapping_df.location_id==location_id].zip_code
        output = zip_code.values
        
    return output

def revgeocode(lat, long, apikey):
    
    # Use google map API to get zipcode based on lat/long
    api = r"https://maps.googleapis.com/maps/api/geocode/json?"
    params = {'latlng': str(lat) + ','+ str(long),
              'key':apikey}
    locale = requests.get(api, params=params)
    locale_json = locale.json()
    
    # parse json file
    zip_codes = [address['long_name'] for i in range(len(locale_json['results']))
                                      for address in locale_json['results'][i]['address_components']
                                      if address['types'][0]=='postal_code']

    # pick most common zipcode
    zipcodes_counter= Counter(zip_codes)
    zipcounter_inv={v:k for k, v in zipcodes_counter.items()}
    zip_code = zipcounter_inv[max(zipcounter_inv.keys())]

    return int(zip_code)

def nextappt(location_ids, url="https://manage-livestage.solvhealth.com/partner/next-available/"):

    """
     Get next available appointment for given location ID(s) based on solvhealth API

     input: location_id (list of str): location ids of next appointment being sought
            url (str): url of solv health next appointment API

     output: (dict) dictionary containing location_id and time (epoch) of next available appointment(s)
    """

    # request appointments for location ids and organize into tuple with respective location
    nextappt_ls = list(zip(location_ids,
                           map(lambda location_id: requests.get(url+location_id),
                               location_ids)))
    
    # clean up api responses and find earliest appointment(s)
    nearby_appts = {}
    min_appt = np.inf
    no_return_error = set()
    http_error = {}
    
    for id_, response in nextappt_ls:

        if response.status_code <= 299 and response.status_code >= 200:

            # if no error response to request, create appt time dict
            resp_json = response.json()
            if len(resp_json):
                
                nearby_appts[id_] = resp_json[0]['epoch_time']

                # select minimum appointment time
                if nearby_appts[id_] < min_appt:
                    min_appt = nearby_appts[id_]
                    
            else:
                no_return_error.add(id_)

        else: 
            if response.status_code in http_error.keys():
                http_error[response.status_code].add(id_)
            else:
                http_error[response.status_code] = {id_}

    if no_return_error:

        # Compose and print error message for location ids API-provided empty returns
        err_dict1={'location_ids': ', '.join(no_return_error) if len(no_return_error)>1 else [v for v in v][0],
                   's': 's' if len(no_return_error)>1 else ''}
        print("No solv API information available for location{s}:\n {location_ids} \n".format(**err_dict1))

    if http_error:        
        
        # Compose and print error message for http errors returned
        for k, v in http_error.items():
            err_dict2={'error_code':k,
                       'location_ids': ', '.join(v) if len(v)>1 else [v for v in v][0],
                       's': 's' if len(v)>1 else ''}
            httperr_str = "HTTP Error {error_code} returned for location{s}:\n{location_ids} \n".format(**err_dict2)
            print(httperr_str)

    # Select appointment(s) with earliest start time
    next_appt = {k:v for k, v in nearby_appts.items() if v == min_appt}

    return next_appt


def main(coord):

    # Provide next appointment date (as epoch time) 
    #    for given lat/long tup input

    availability = True

    apikey = input("Input google geocode api key:")
    zip_code = revgeocode(coord[0], coord[1], apikey)

    location_ids = ziptolocation(zip_code)
    
    appointment_time = nextappt(location_ids)

    # Collision behavior not well-defined in technical specs:
    #    Return all location ids if earliest times available in two or more places.
    location_ids = set()
    earliestappt_dict = {}
    earliestappt_ls = []

    for k, v in appointment_time.items():
        # Only add appointment dictionary if location is unique
        if k not in location_ids:
            location_ids.add(k)
            earliestappt_dict = {'location_id': k, 'appointment_time': v}
            earliestappt_ls.append(earliestappt_dict)
    
    # Adding 'appointments' supercategory to JSON output to handle collisions where two or more location IDs have same earliest available appointment.
    appointments_dict = {'appointments':earliestappt_ls}

    # No appointments available error
    if not earliestappt_ls:
        
        availability = False
        print("No appointments available for specified location")
     
    return json.dumps(appointments_dict, indent=4)


# Provided test cases
if __name__ == '__main__':

    from test import TestRevGeoCode, TestNextAppt, TestMainCode

    # Slightly-informally cramming tests into same module as code
    test_revgeocode = TestRevGeoCode()
    test_nextappt = TestNextAppt()
    test_main = TestMainCode()

    testresult = {'reverse geocode API unit test': test_revgeocode.test_revgeocode(),
                   'next appointment unit test': test_nextappt.test_nextappt(),
                   'smoke test': test_main.test_mainnoerrors(),
                   'returns json test': test_main.test_mainreturnsjson()}
    print("All {} tests passed! Including: {}".format(len(testresult), ", ".join(testresult.keys())))

