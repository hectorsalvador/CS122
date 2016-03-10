## Read json files containing information of businesses on each neighborhood
## Assign scores to each establishment

import json
import numpy
import queue    			#check that name is "Queue" with Python 2.7
from datetime import date
from math import radians, degrees, cos, sin, asin, atan2, sqrt
import os
import re

KEY_FILE = "gsm_key.txt"
MONTH_DAYS = 30
RATING_SCORE_ADJ = 1 / 5
MAX_SCORE = 1
PM_HOURS = 1200
EARTH_RADIUS = 6371 # KM. Use 3956 for miles.
HORZ = 512
VERT = 512
PATH_1 = '/home/student/cs122-win-16-cgrandet-hectorsalvador/cs_project/ui/neigborhoods'
PATH_2 = '/home/student/cs122-win-16-cgrandet-hectorsalvador/cs_project/ui/scoring'
DAY_DICT = {"Monday":"Mon","Tuesday":"Tue","Wednesday":"Wed","Thursday":"Thu","Friday":"Fri","Saturday":"Sat","Sunday":"Sun"}

args1 = args_to_ui = {
  "time_start": 900,
  "attr_rest": [
    "Hipster"
  ],
  "neigh": "Hyde Park",
  "day": "Monday",
  "time_end": 2300,
  "est": [
    "Restaurants",
    "Nightlife"
  ],
  "attr_club": [
    "Karaoke"
  ]
}

def run_score(args_from_ui):
    neigh_name = args_from_ui["neigh"]
    filename = neigh_name+"_dict.json"
    categories = args_from_ui["est"]
    day_formal = args_from_ui["day"]
    day = DAY_DICT[day_formal] 
    matching_words = args_from_ui.get("attr_rest",[])
    min_hour = args_from_ui.get("time_start",-1)
    max_hour = args_from_ui.get("time_end",-1)
    results = go(filename,categories,day,matching_words,min_hour,max_hour)
    print(results)
    url, color_label = map_url(results)
    header, table = gen_table(results)

    return (url, color_label, header, table,)


def go(filename, categories, day, matching_words = [], min_hour = - 1, \
	max_hour = - 1):
	'''
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
		A string with the path to a json file with information on businesses 
	Output:
		A list of Biz objects, containing the information of businesses in the
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
		address = [import_address(data[biz])]
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
	'''
	if len(biz_list) != 0:
		for biz in biz_list:
			biz._set_score(score(biz, biz_list, matching_words))

def filter_businesses(biz_list, categories, day, min_hour, max_hour):
	'''
	Inputs:
		biz_list, a list of Biz objects 
		categories, a list of strings referring to desired businesses 
			(e.g ["delis", "cafes", "museums"])
		min_hour, an int in 0000 format (e.g. 6:00 AM is 0600)
		max_hour, an int in the same format as min_hour
		day, a string indicating the day (e.g. "Mon", "Sat")
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
	best_list = []
	for key, value in biz_list.items():
		for biz in value:
			best_list.append([key, biz[1], biz[0][1].name, biz[0][1].address[0]])
			print("Category: {}, Business {}: {}, Address: {}, ".format(\
				key, biz[1], biz[0][1].name, biz[0][1].address[0]))
	return best_list


def gen_table(biz_dict):
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
	address = biz_dict.get("address", None)
	if address != None and len(address) != 0:
		return address[0]

def score(biz, biz_list, matching_words):
	'''
	'''
	rating = calculate_score_ratings(biz)
	price = calculate_score_price(biz)
	match = calculate_score_matches(biz, matching_words)
	dist = calculate_score_distance(biz, biz_list)
	return rating + price + match + dist

def calculate_score_ratings(biz):
	'''
	if no comments, it doesn't load into the .json
	'''
	today = date.today()
	sum_weights = 0
	rv = 0
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
	If no "$", it doesn't load into the .json
	'''
	price_range = len(biz.price)
	if price_range == 1:
		return MAX_SCORE
	else:
		return MAX_SCORE / 2

def calculate_score_distance(biz, biz_list):
	'''

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
	Inputs:
		biz_list, is a list of Biz objects
	Returns:
		(lat, lon), a tuple indicating the weighted centroid of the businesses 
		in the neighborhood
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
	center is a tuple with (lat, lon)
	biz_list, a list of Biz objects used to calculate distance score
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
	'''
	dummy1 = time_str.split()
	dummy2 = dummy1[0].split(":")
	hour = int(dummy2[0]+dummy2[1])
	if dummy1[1] in ["am", "Am", "AM"]:
		return hour
	else:
		return hour + PM_HOURS

##################################
#####       Biz class        #####
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

##################################
#####          GO            #####
##################################

# if __name__ == "__main__":
# 	filename = 'The Loop_dict.json'
# 	c1 = ['Delis','Bagels']
# 	mw1 = []
# 	b1 = go(filename, c1, "Tue", mw1, 1000, 1800)
# 	url1 = map_url(b1)
# 	print(url1)
# 	rv1 = print_output(b1)

# 	mw2 = ['Casual', 'Take-out', 'Caters', 'Good for Kids']
# 	c2 = ['Delis']
# 	b2 = go(filename, c2, "Tue", mw2)
# 	url2 = map_url(b2)
# 	print(url2)
# 	rv2 = print_output(b2)



#Stuff we found on the project:
#got banned from yelp
#took too long to retrieve all the comments
#decided instead to take a simplified approach
#google static maps api
