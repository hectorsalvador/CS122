##
##
## Read json files containing information of businesses on each neighborhood
## Assign scores to each establishment

import json
import numpy
import queue    			#check that name is "Queue" with Python 2.7
from datetime import date
from math import radians, degrees, cos, sin, asin, atan2, sqrt

## We have to check how will min and max times will work
## they are in the filter_businesses function

MONTH_DAYS = 30
RATING_SCORE_ADJ = 1 / 5
MAX_SCORE = 1
PM_HOURS = 1200
DEGREES_IN_PI_RADIANS = 180
EARTH_RADIUS = 6371 # KM. Use 3956 for miles.
HORZ = 512
VERT = 512

def go(filename, categories, matching_words, min_hour, max_hour, day):
	'''
	'''
	biz_list = create_biz_list(filename)
	assign_scores(biz_list, matching_words)
	filtered_biz_list = filter_businesses(biz_list, categories, min_hour, \
		max_hour, day)
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
	biz_list = []

	with open(filename) as d:
		data = json.load(d)

	for biz in data:
		neighborhoods = data[biz].get("neighborhoods", None)
		# print(type(neighborhoods))
		price = data[biz].get("price", None)
		# print(type(price))
		comments = data[biz].get("comments", None)
		# print(type(comments))
		times = data[biz].get("times", None)
		# print(type(times))
		lat = data[biz].get("latitude", None)
		# if lat == None:
		# 	print(biz)
		lon = data[biz].get("longitude", None)
		# print(type(lon))
		attributes = data[biz].get("attributes", None)
		# print(type(attributes))
		if attributes != None:
			attributes = attributes.get("Ambience", None)
		#attributes is only getting "Ambience", should we include further
		#options for attributes?
		categories = data[biz].get("categories", None)
		# print(type(categories))
		address = data[biz].get("address", None)
		# print(type(address))
		if None in [neighborhoods, price, comments, times, lat, lon, \
			attributes, categories, address]:
			pass
		else:
			biz = Biz(biz, neighborhoods, price, comments, times, lat, lon, \
				attributes, categories, address)
			biz_list.append(biz)

	return biz_list

def assign_scores(biz_list, matching_words, verbose = False):
	for biz in biz_list:
		biz._set_score(score(biz, biz_list, matching_words, verbose))

def filter_businesses(biz_list, categories, min_hour, max_hour, day, 
	verbose = False):
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
	i = 0
	for biz in biz_list:
		if verbose:
			print("Checking {}..".format(biz.name))
			print("  Categories: {}".format(biz.categories))
		dummy = False
		if len(biz.categories) > 1:
			for elem in biz.categories:
				if any(i in categories for i in elem):
					dummy = True
					if verbose:
						print("   {}".format(dummy))
		else:
			if any(i in categories for i in biz.categories):
				if verbose:
					print("   {}".format(dummy))
				dummy = True

		if dummy:
			if verbose:
				print("   Times: {}".format(biz.times))
			if (biz.times == None) or (len(biz.times[day]) == 0):
				i += 1
				if verbose:
					print("  No times or schedule: {}".format(i))
					print("    Adding {} to the list".format(biz.name))
				new_biz_list.append(biz)
			elif (max_hour >= hourize(biz.times[day][0])) and \
			(min_hour <= hourize(biz.times[day][1])):
				if verbose:
					print("  {} has times and schedule.".format(biz.name))
					print("    Adding {} to list.".format(biz))
				new_biz_list.append(biz)
		else:
			if verbose:
				print("    Not in categories.")

	if verbose:
		print([biz.name for biz in new_biz_list])
	return new_biz_list

def best_biz_by_categories(new_biz_list, categories, verbose = False):
	d = {}
	for category in categories:
		d.setdefault(category, queue.PriorityQueue(3))
	for biz in new_biz_list:
		if verbose:
			print("Checking {}".format(biz.name))
		for category in biz.categories:
			if category[0] in categories:
				if verbose:
					print("   Is {}".format(category[0]))
				if not d[category[0]].full():
					if verbose:
						print("      Adding {} to {} queue.".format(biz.name,\
							category[0]))
						print("      Score: {}".format(biz.score))
					d[category[0]].put((biz.score, biz))
				else:
					lowest_biz = d[category[0]].get()
					if biz.score > lowest_biz[0]:
						d[category[0]].put((biz.score, biz))
						if verbose:
							print("      Adding {} to {} queue.".format(\
								biz.name, category[0]))
							print("      Score: {}".format(biz.score))
					else:
						d[category[0]].put(lowest_biz)
						if verbose:
							print("      {} was not added to {} queue.".format(\
								biz.name, category[0]))
							print("      Score: {}".format(biz.score))
			else:
				if verbose:
					print("   Not looking for {}".format(category[0]))
	dprime = {}
	for key in d.keys():
		dprime.setdefault(key, [])
		i = d[key].qsize()
		while not d[key].empty():
			dprime[key].append((d[key].get(), i))	
			i = i - 1

	return dprime

def map_url(best_biz):

	# Valid colors taken from Google Static Maps API
	COLORS = ["red", "green", "purple", "yellow", "blue", "orange",\
	"gray", "white", "black", "brown"]

	url_init = "https://maps.googleapis.com/maps/api/staticmap?"
	size = "size={}x{}".format(HORZ, VERT)
	maptype = "maptype=roadmap"

	markers_list = []
	i = 0
	for key in best_biz.keys():
		color = COLORS[i]
		color_url = "color:{}".format(color)

		for biz in best_biz[key]:
			label = biz[1]
			label_url = "label:{}".format(label)	
			address = biz[0][1].address[0]
			address_url = address.replace(" ", "+") + ",Chicago"
			marker = "markers=" + "%7C".join([color_url, label_url, address_url])
			markers_list.append(marker)

		i += 1

	markers = "&".join(markers_list)
	key = "key=AIzaSyCyV611rvT1sv6CHSxy9HOexs6iznpPZPA"
	url_end = "&".join([size, maptype, markers, key])
	url = url_init + url_end

	return url

##################################
#####    Helper functions    #####
##################################

def score(biz, biz_list, matching_words, verbose = False):
	'''
	'''
	rating = calculate_score_ratings(biz)
	price = calculate_score_price(biz)
	match = calculate_score_matches(biz, matching_words)
	dist = calculate_score_distance(biz, biz_list)

	if verbose:
		print("Rating score: {}".format(rating))
		print("Price score: {}".format(price))
		print("Match score: {}".format(match))
		print("Distance score: {}".format(dist))

	return rating + price + match + dist

def calculate_score_ratings(biz):
	'''
	'''
	today = date.today()
	sum_weights = 0
	rv = 0
	for comment in biz.comments:
		d = biz.comments[comment]["date"]
		c_date = date(d[0], d[1], d[2])
		diff = int(str(today - c_date).split()[0])
		weight = min(1, MONTH_DAYS / diff)
		sum_weights += weight
		weighted_rating = weight * int(biz.comments[comment]["rating"])
		rv += weighted_rating
	return rv / sum_weights * RATING_SCORE_ADJ

def calculate_score_price(biz):
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
#####                        #####
##################################

if __name__ == "__main__":
	filename = 'The Loop_dict.json'
	categories = ['Delis', 'Bagels', 'Museums', 'Middle Eastern']
	matching_words = ['Casual']
	best = go(filename, categories, matching_words, 1000, 1800, "Tue")
	url = map_url(best)
	print(url)
