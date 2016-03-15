#Cheap Chicago - Final project for CS122

# Carlos O. Grandet Caballero
# Hector Salvador Lopez

'''
This code is mainly used to clean the data and generate the entries for the
form, it is simply a set of helping functions that allowed us to homogeneize 
and clean the data from the neighborhood dictionaries. 
'''
import os
import json
import glob  
import csv 
import re 

PATH = '/home/student/cs122-win-16-cgrandet-hectorsalvador/cs_project/ui/neigborhoods'

def gen_categories(neighborhood_filename,relationship_filename):
	'''
	Given a relationship of categories and subcategories from Yelp,
	relate each business to a category and update the neighborhood dictionary
	Input: 
	neighborhood_filename: a filename that contains YELP information for a neighborhood
	relationship_filename: a filename that contains the relationship between categories 
	and subcategories in the YELP nomenclature.
	Output
	Two files, the updated neighborhood dictionary and a new dictionary
	that relates each subcategory to a parent. 
	'''
	with open(neighborhood_filename,"r") as a:
		neigh_dict = json.load(a)

	with open(relationship_filename,"r") as b:
		relationship_dict = json.load(b)

	category_dict = {}
	for item in relationship_dict:
		category_dict[item["title"]]= item["parents"][0]

	for biz in neigh_dict:
		subcategories = neigh_dict[biz][categories]
		for item in subcategories:
			for subitem in item:
				if subitem in list(category_dict.keys()):
					neigh_dict[biz]["category"] = category_dict[subitem]

	for keys,values in category.items():

	with open(neighborhood_filename, "w") as c:
	    json.dump(neigh_dict,c)

	with open("categories_final", "w") as c:
	    json.dump(neigh_dict,c)



def obtain_form_entries(neighborhoods_form,categories_form,attributes_form):
	'''
	Creates csv files that will act as fields for the form of the Django website
	Input: 
	neighborhoods_form: the name of the csv filename that will contain the neighborhoods
	categories_form: the name of the csv filename that will contain the categories
	attributes_form: the name of the csv filename that will contain the attributes

	Output
	Three csv files
	'''
	with open("categories_final.json", "r") as b:
	    categories_json = json.load(b)

	categories_set = set()
	neighborhood_set = set()
	attributes_dict = {}


	for filename in os.listdir(path):
		neighborhood_name = re.search("([A-Za-z-' ]+)(_dict+)",filename).group(1)
		file_dir = os.path.join(path, filename)
		neighborhood_set.add(neighborhood_name)
		
		with open(file_dir, "r") as b:
		    biz_dict = json.load(b)
		
		for biz in biz_dict:
			biz_category = biz_dict[biz].get("category",None)
			categories_set.add(biz_category)
			if category_value != None:
				attributes_set = attributes_dict.get(biz_category,set())
				if "attributes" in biz_dict[biz].keys():
					biz_attributes = biz_dict[biz]["attributes"]
					for key,value in biz_attributes.items():
						attributes_set.add((key,value))
						attributes_dict[biz_category] = attributes_set
			else:
				biz_dict[biz]["attributes"] = None

	#Transform set of values into list 
	for key,values in attributes_dict.items():
		attributes_dict[key] = list(values)

	with open(attributes_form, "w") as c:
	    json.dump(attributes_dict,c)

	for key in sorted(list(attributes_dict.keys())):
		
		cat_file = open(categories_form, 'w')
		w1 = csv.writer(cat_file, delimiter=",")
		w1.writerow([key])
		cat_file.close()


		attr_file = open('attributes_'+key+".csv", 'w')
		w = csv.writer(attr_file, delimiter=",",skipinitialspace=True)
		for attr,value in attributes_dict[key]:
			w.writerow([attr,value])
		attr_file.close()

	
	neigh_file = open(neighborhoods_form, 'w')
	w2 = csv.writer(neigh_file, delimiter=",")
	for neighborhood in sorted(list(neighborhood_set)):
		w2.writerow([neighborhood])
	neigh_file.close()



