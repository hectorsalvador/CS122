# Cheap Chicago - Final project for CS122
# Carlos O. Grandet Caballero
# Hector Salvador Lopez

# ORIGINAL CODE, except when otherwise noted
# Reads json files containing information of establishments on each neighborhood
# Assigns scores to each establishment and selects the best scored
# Returns information to display on django-based web interface

import json
import numpy
import queue
from datetime import date
from math import radians, degrees, cos, sin, asin, atan2, sqrt
import os
import re

KEY_FILE = "gsm_key.txt"
MONTH_DAYS = 30
RATING_SCORE_ADJ = 1 / 5
MAX_SCORE = 1
PM_HOURS = 1200
EARTH_RADIUS = 6371 # KM
HORZ = 512
VERT = 512
PATH_1 = '/home/student/cs122-win-16-cgrandet-hectorsalvador/cs_project/ui/neigborhoods'
PATH_2 = '/home/student/cs122-win-16-cgrandet-hectorsalvador/cs_project/ui/scoring'

DAY_DICT = {"Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed", \
"Thursday": "Thu", "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun"}

def run_score(args_from_ui):
    '''
    Inputs:
        args_from_ui, a dictionary with information introduced by user
        EXAMPLE
        args_to_ui = {"time_start": 900, "attr_rest": ["Hipster"],
            "neigh": "Hyde Park", "day": "Monday", "time_end": 2300,
            "est": ["Restaurants", "Nightlife"],
            "attr_club": ["Karaoke"]}
    Outputs:
        A tuple with information required by "/ui/search/views.py"
    '''
    neigh_name = args_from_ui["neigh"]
    filename = neigh_name + "_dict.json"
    categories = args_from_ui["est"]
    day_formal = args_from_ui["day"]
    day = DAY_DICT[day_formal] 
    matching_words = args_from_ui.get("attr_rest",[])
    min_hour = args_from_ui.get("time_start", -1)
    max_hour = args_from_ui.get("time_end", -1)
    results = go(filename,categories,day,matching_words,min_hour,max_hour)
    print(results)
    url, color_label = map_url(results)
    header, table = gen_table(results)

    return (url, color_label, header, table)


def go(filename, categories, day, matching_words = [], min_hour = - 1, \
    max_hour = - 1):
    '''
    Inputs:
        filename, string with the path to a json file with information on 
            businesses/places
        categories, a list of strings that will filter the category of 
            business/place shown to final user (e.g ["Restaurants", "Food"])
        day, a string indicating the day of the week (e.g. "Mon", "Sat")
        matching_words, a list of strings to find in the attributes element
            of a business/place (e.g ["Lunch", "Casual"])
        min_hour and max_hour, ints indicating the timeframe where the end 
            user will expect to go to a business/place. Must be in 0000 format 
            (e.g. 6:00 AM is 0600)
    Output:
        A dictionary with categories sought as keys, and best establishments
            as items in a priority queue
    '''
    biz_list = create_biz_list(filename)
    assign_scores(biz_list, matching_words)
    filtered_biz_list = filter_businesses(biz_list, categories, day, min_hour,\
        max_hour)
    best_biz = best_biz_by_categories(filtered_biz_list, categories)
    return best_biz

def create_biz_list(filename):
    '''
    Inputs:
        filename, string with the path to a json file with information on 
            establishments 
    Output:
        A list of Biz objects, containing the information of establishments in the
            given json file
    '''
    with open(os.path.join(PATH_1, filename), "r") as d:
        data = json.load(d)

    biz_list = []
    count_g = 0
    count_b = 0
    for biz in data:
        neighborhoods = data[biz].get("neighborhoods", None)
        price = data[biz].get("price", None)
        comments = data[biz].get("comments", None)
        times = data[biz].get("times", None)
        lat = data[biz].get("latitude", None)
        lon = data[biz].get("longitude", None)
        attributes = import_attributes(data[biz])
        category = data[biz].get("category", None)
        address = import_address(data[biz])
        if None in [neighborhoods, price, comments, times, lat, lon, \
            attributes, category, address]:
            count_b += 1
            pass
        else:
            biz = Biz(biz, neighborhoods, price, comments, times, lat, lon, \
                attributes, category, address)
            biz_list.append(biz)
            count_g += 1
    print(count_g,count_b)
    print(len(biz_list))
    return biz_list

def assign_scores(biz_list, matching_words):
    '''
    Inputs:
        biz_list, a list of Biz objects
        matching_words, a list of strings to find in the attributes element
            of a establishments
    '''
    if len(biz_list) != 0:
        for biz in biz_list:
            biz._set_score(score(biz, biz_list, matching_words))

def filter_businesses(biz_list, categories, day, min_hour, max_hour):
    '''
    Inputs:
        biz_list, a list of Biz objects 
        categories, a list of strings referring to desired establishments 
            (e.g ["Restaurants", "Arts"])
        min_hour, an int in 0000 format (e.g. 6:00 AM is 0600)
        max_hour, an int in the same format as min_hour
        day, a string indicating the day (e.g. "Mon", "Sat")
    Output:
        A list of Biz objects, filtered according to inputs
    '''
    new_biz_list = []
    if len(biz_list) == 0:
        return new_biz_list
    
    for biz in biz_list:
        dummy = False
        if biz.categories in categories:
            dummy = True
    
        if dummy:
            if (max_hour == -1) and (min_hour == -1):
                new_biz_list.append(biz)
            elif (biz.times == None) or (len(biz.times[day]) == 0):
                new_biz_list.append(biz)
            elif (max_hour >= hourize(biz.times[day][0])) and \
            (min_hour <= hourize(biz.times[day][1])):
                new_biz_list.append(biz)
    print(len(new_biz_list))
    return new_biz_list

def best_biz_by_categories(new_biz_list, categories):
    '''
    Inputs:
        new_biz_list, a filtered list of Biz objects 
        categories, a list of strings referring to desired establishments 
            (e.g ["Restaurants", "Arts"])
    Output:
        A dictionary with categories sought as keys, and best scoring 
            establishments as items in a priority queue
    '''
    d = {}
    if len(new_biz_list) == 0:
        return d

    for category in categories:
        d.setdefault(category, queue.PriorityQueue(3))
    
    for biz in new_biz_list:
        if biz.categories in categories:
            if not d[biz.categories].full():
                d[biz.categories].put((biz.score, biz))
            else:
                lowest_biz = d[biz.categories].get()
                if biz.score > lowest_biz[0]:
                    d[biz.categories].put((biz.score, biz))
                else:
                    d[biz.categories].put(lowest_biz)
    dprime = {}
    for key in d.keys():
        dprime.setdefault(key, [])
        i = d[key].qsize()
        while not d[key].empty():
            dprime[key].append((d[key].get(), i))   
            i = i - 1
    return dprime

def map_url(best_biz):
    '''
    Inputs:
        best_biz, a dictionary with best scoring establishments as items in a 
            priority queue
    Outputs:
        A url with the path to a Google Static Maps API map
    '''
    # Valid colors taken from Google Static Maps API
    COLORS = ["red", "green", "purple", "yellow", "blue", "orange",\
    "gray", "white", "black", "brown"]

    url_init = "https://maps.googleapis.com/maps/api/staticmap?"
    size = "size={}x{}".format(HORZ, VERT)
    maptype = "maptype=roadmap"

    markers_list = []
    i = 0
    color_label = {}
    for key in best_biz.keys():
        color = COLORS[i]
        color_url = "color:{}".format(color)
        color_label[key] = color

        for biz in best_biz[key]:
            label = biz[1]
            label_url = "label:{}".format(label)    
            address = biz[0][1].address[0]
            address_url = address.replace(" ", "+") + ",Chicago"
            marker = "markers=" + "%7C".join([color_url, label_url, address_url])
            markers_list.append(marker)

        i += 1

    markers = "&".join(markers_list)

    f = open(os.path.join(PATH_2, KEY_FILE))
    key = "key={}".format(f.readline()) 
    url_end = "&".join([size, maptype, markers, key])
    url = url_init + url_end
    return url, color_label


##################################
#####    Helper functions    #####
##################################

def print_output(biz_list):
    '''
    
    '''
    best_list = []
    for key, value in biz_list.items():
        for biz in value:
            best_list.append([key, biz[1], biz[0][1].name, biz[0][1].address[0]])
            print("Category: {}, Business {}: {}, Address: {}, ".format(\
                key, biz[1], biz[0][1].name, biz[0][1].address[0]))
    return best_list


def gen_table(biz_dict):
    '''
    Inputs:
        biz_dict, a dictionary containing the information of an establishment
    Outputs:
        a tuple with headers and a list of lists containing information of the
            best scoring establishments
    '''
    headers = ["Category", "Ranking", "Business", "Address"]
    best_list = []
    for key, value in biz_dict.items():
        value.sort(key = lambda x: x[1])
        for biz in value:
            name = re.search("(.+)-chicago",biz[0][1].name).group(1)
            name = " ".join(name.split("-")).upper()
            best_list.append([key,biz[1], name, biz[0][1].address[0]])
    return (headers, best_list)


def import_attributes(biz_dict):
    '''
    Inputs:
        biz_dict, a dictionary containing the information of an establishment
    Output:
        a list with strings related to the attributes of an establishment
    '''
    attributes = biz_dict.get("attributes", None)
    rv = []
    if attributes == None:
        return attributes
    else:
        for key, value in attributes.items():
            if value == "Yes":
                rv.append(key)
            elif key == "Ambience":
                if type(attributes["Ambience"]) == list:
                    for i in attributes["Ambience"]:
                        rv.append(i)
                else:
                    rv.append(attributes["Ambience"])
            elif key == "Good For":
                list_attributes = value.split(",")
                for attr in list_attributes:
                    rv.append(attr)
            elif value != "No":
                rv.append("{} {}".format(key, value))
        return rv

def import_address(biz_dict):
    '''
    Inputs:
        biz_dict, a dictionary containing the information of an establishment
    Output:
        a string or a None, depending on whether the address is in an adequate 
            format for the city of Chicago
    '''
    address = biz_dict.get("address", None)
    number = '[0-9]+'
    card_pt = '[NSEW ]'
    name = ".+"
    valid_address = ' '.join([number, card_pt, name])
    if address == None or len(address) == 0 or \
        len(re.findall(valid_address, address[0])) == 0:
        return None
    elif re.findall(valid_address, address[0])[0] != address[0]:
        return None
    else:
        return address

def score(biz, biz_list, matching_words):
    '''
    Inputs:
        biz, a Biz object
        biz_list, a list of Biz objects
        matching_words, a list of strings to find in the attributes element
            of a business/place (e.g ["Lunch", "Casual"])
    Outputs:
        an int between 0 and 4 representing a score 
    '''
    rating = calculate_score_ratings(biz)
    price = calculate_score_price(biz)
    match = calculate_score_matches(biz, matching_words)
    dist = calculate_score_distance(biz, biz_list)
    return rating + price + match + dist

def calculate_score_ratings(biz):
    '''
    Inputs:
        biz, a Biz object
    Outputs:
        an int, representing a ratings score between 0 and 1
    '''
    today = date.today()
    sum_weights = 0
    rv = 0
    # if no comments, it doesn't load into the .json
    if len(biz.comments) != 0:
        for comment in biz.comments:
            d = biz.comments[comment]["date"]
            c_date = date(d[0], d[1], d[2])
            diff = int(str(today - c_date).split()[0])
            weight = min(1, MONTH_DAYS / diff)
            sum_weights += weight
            weighted_rating = weight * int(biz.comments[comment]["rating"])
            rv += weighted_rating
        return rv / sum_weights * RATING_SCORE_ADJ
    else:
        return 0

def calculate_score_price(biz):
    '''
    Inputs:
        biz, a Biz object
    Outputs:
        an int, representing a price score between 0 and 1
    '''
    price_range = len(biz.price)
    if price_range == 1:
        return MAX_SCORE
    else:
        return MAX_SCORE / 2

def calculate_score_distance(biz, biz_list):
    '''
    Inputs:
        biz, a Biz object
        biz_list, a list of Biz objects
    Outputs:
        an int, representing a distance score between 0 and 1
    '''
    center = find_biz_weighted_centroid(biz_list)
    max_dist = calculate_farthest_biz(center, biz_list)
    lat0 = biz.lat
    lon0 = biz.lon
    lat1 = center[0]
    lon1 = center[1]
    return haversine_distance(lon0, lat0, lon1, lat1) / max_dist

def calculate_score_matches(biz, matching_words):
    '''
    Inputs:
        biz, a Biz object
        matching_words, a list of strings to find in the attributes element
            of a business/place (e.g ["Lunch", "Casual"])
    Outputs:
        an int, representing a match score between 0 and 1
    '''
    tot = len(matching_words)
    score = 0
    if tot == 0:
        return 1
    elif biz.attributes == None:
        return 0
    else:
        for word in matching_words:
            if word in biz.attributes:
                score += 1
        return score / tot

def find_biz_weighted_centroid(biz_list):
    '''
    MODIFIED
    Followed instructions from: http://www.geomidpoint.com/calculation.html

    Inputs:
        biz_list, is a list of Biz objects
    Returns:
        (lat, lon), a tuple indicating the weighted geographic center of the 
        establishments in the neighborhood
    '''
    weights = [calculate_score_ratings(biz) + calculate_score_price(biz) \
        for biz in biz_list]

    #convert lat and lon to radians
    lats = [radians(biz.lat) for biz in biz_list]
    lons = [radians(biz.lon) for biz in biz_list]

    # convert to cartesian coordinates
    x = [cos(lats[i]) * cos(lons[i]) for i in range(len(lats))]
    y = [cos(lats[i]) * sin(lons[i]) for i in range(len(lats))]
    z = [sin(lats[i]) for i in range(len(lats))]

    # compute weighted average
    xc = 0
    yc = 0
    zc = 0
    for i in range(len(weights)):
        xc += x[i] * weights[i]
        yc += y[i] * weights[i]
        zc += z[i] * weights[i]
    midpt = [xc / sum(weights), yc / sum(weights), zc / sum(weights)]

    # go back to degrees
    lon = degrees(atan2(yc, xc))
    hyp = sqrt(xc ** 2 + yc ** 2)
    lat = degrees(atan2(zc, hyp))

    return (lat, lon)

def calculate_farthest_biz(center, biz_list):
    '''
    Inputs:
        center, a tuple of floats with (lat, lon)
        biz_list, a list of Biz objects used to calculate distance score
    Output:
        an int with the longest distance from the weighted geographic center
            of establishments
    '''
    far_biz = None
    max_dist = 0
    lat0 = center[0]
    lon0 = center[1]
    for biz in biz_list:
        lat1 = biz.lat
        lon1 = biz.lon
        dist = haversine_distance(lon0, lat0, lon1, lat1)
        if dist > max_dist:
            far_biz = biz
            max_dist = dist
    return max_dist

def haversine_distance(lon0, lat0, lon1, lat1):
    '''
    DIRECT COPY - PA 2: Course Search Engine Part 1
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    '''
    lon0, lat0, lon1, lat1 = map(radians, [lon0, lat0, lon1, lat1])
    dlon = lon1 - lon0
    dlat = lat1 - lat0 
    a = sin(dlat / 2) ** 2 + cos(lat0) * cos(lat1) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a)) 
    return c * EARTH_RADIUS

def hourize(time_str):
    '''
    Inputs:
        time_str, a string indicating an hour (e.g. "9:00 AM")
    Outputs:
        an int with hour in a military format (e.g. 900)
    '''
    dummy1 = time_str.split()
    dummy2 = dummy1[0].split(":")
    hour = int(dummy2[0]+dummy2[1])
    if dummy1[1] in ["am", "Am", "AM"]:
        return hour
    else:
        return hour + PM_HOURS

##################################
#####  Biz class: ORIGINAL   #####
##################################

class Biz(object):

    def __init__(self, name, neighborhoods, price, comments, times,
        lat, lon, attributes, categories, address):
        self._name = name
        self._neighborhoods = neighborhoods
        self._price = price
        self._comments = comments
        self._times = times
        self._lat = lat
        self._lon = lon
        self._attributes = attributes
        self._categories = categories
        self._address = address
        self._score = 0

    @property
    def name(self):
        return self._name

    @property
    def lat(self):
        return self._lat

    @property 
    def lon(self):
        return self._lon

    @property
    def comments(self):
        return self._comments

    @property 
    def price(self):
        return self._price

    @property
    def attributes(self):
        return self._attributes

    @property 
    def times(self):
        return self._times

    @property 
    def categories(self):
        return self._categories

    @property
    def address(self):
        return self._address

    @property 
    def score(self):
        return self._score

    def _set_score(self, score):
        self._score = score
