##
##

## Assign scores to establishments

import numpy
from datetime import date
from math import radians, cos, sin, asin, sqrt

EARTH_RADIUS = 6371 # KM. Use 3956 for miles.

def haversine_distance(lon0, lat0, lon1, lat1):
    '''
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians 
    lon0, lat0, lon1, lat1 = map(radians, [lon0, lat0, lon1, lat1])
    dlon = lon1 - lon0
    dlat = lat1 - lat0 
    a = sin(dlat / 2)**2 + cos(lat0) * cos(lat1) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a)) 
    return c * EARTH_RADIUS


def find_business_epicenter(businesses):
	'''
	businesses are a dictionary or list of Biz objects
	Epicenter is determined by taking the weighted haversine distance 
	'''
	pass

def calculate_largest_distance(businesses):
	'''
	businesses are a dictionary or list of Biz objects
	'''
	pass

class Biz(object):

	RATING_SCORE_ADJ = 1 / 5
	MONTH_DAYS = 30
	MAX_SCORE = 1

	def __init__(self, name, neighborhoods, price, comments, times, reviews,
		lat, lon, attributes, categories):
		self._name = name
		self._neighborhoods = neighborhoods
		self._price = price
		self._comments = comments
		self._times = times
		self._reviews = reviews
		self._lat = lat
		self._lon = lon
		self._attributes = attributes
		self._categories = categories

		self._score_ratings = self._calculate_score_ratings()
		self._score_price = self._calculate_score_price()

	def _calculate_score_ratings(self):
		'''
		'''
		today = date.today()
		rv = 0
		for comment in self._comments:
			d = comment["date"]
			c_date = date(d[0], d[1], d[2])
			weight = min(1, MONTH_DAYS / (today - c_date))
			weighted_rating = weight * int(comment["rating"])
			rv += weighted_rating
		return rv * RATING_SCORE_ADJ

	def _calculate_score_price(self):
		price_range = len(self._price)
		if price_range == 1:
			return MAX_SCORE
		else:
			return MAX_SCORE / 2

	def _calculate_score_matches(self, matching_words):
		pass

	def _calculate_score_distance(self, center, max_distance):
		'''
		center is a tuple (lat, lon)
		max distance is an integer
		'''
		lat1 = center[0]
		lon1 = center[1]
		rv = (max_distance - haversine_distance(self._lon, self._lat, lon1, \
			lat1)) / max_distance
		return rv

	def score(self, matching_words, center, max_distance):
		score = self._calculate_score_ratings() + \
		self._calculate_score_price() + \
		self._calculate_score_matches(matching_words) + \
		self._calculate_score_distance(center, max_distance)
		return score

def compute_distance_matrix(list_of_clusters):
	n = len(list_of_clusters)
	dmatrix = []
	for i in range(n):
		row = []
		for j in range(n):
			ij = list_of_clusters[i].distance_to(list_of_clusters[j])
			row.append(ij)
		dmatrix.append(row)
	dmatrix = numpy.matrix(dmatrix)

	return dmatrix


class Cluster(object):

	def __init__(self, name, lat, lon):
		self._name = name
		self._lat = lat
		self._lon = lon
		self._is_leaf = True

		# self._subclusters = []
		# self._leafs = []
		# self._left = None
		# self._right = None
		# self._dist = 0

	def distance_to(self, other):
		lon0 = self._lon
		lat0 = self._lat
		lon1 = other._lon
		lat1 = other._lat
		hdist = haversine_distance(lon0, lat0, lon1, lat1)
		return hdist


	# def merge_clusters(self, left, right, dist):
	# 	self._leaf = False
	# 	self._left = left
	# 	self._right = right
	# 	self._dist = dist
	# 	if left._is_leaf:
	# 		self._leafs.append(left)
	# 	else:
	# 		self._leafs += left._leafs
	# 	if right._is_leaf:
	# 		self._leafs.append(right)
	# 	else:
	# 		self._leafs += right._leafs
	# 	self._subclusters.append(left)
	# 	self._subclusters.append(right)

	# def __repr__(self):
	# 	if self._is_leaf:
	# 		print(self._id)
	# 	else:
	# 		print(self._subclusters)







