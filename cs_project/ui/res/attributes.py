import os
import json
import glob  
import csv 
import re 

path = '/home/student/cs122-win-16-cgrandet-hectorsalvador/cs_project/ui/neigborhoods'
# files=glob.glob(path) 
# print(files)  
# for filename in files:
# 	print(filename)


categories_set = set()
neighborhood_set = set()
attributes_type = {}

with open("categories_final.json", "r") as b:
    categories_json = json.load(b)

count = 0 
print("test")
count = 0
for filename in os.listdir(path):
	neighborhood_name = re.search("([A-Za-z-' ]+)(_dict+)",filename).group(1)
	file_dir = os.path.join(path, filename)
	neighborhood_set.add(neighborhood_name)
	print(file_dir)
	with open(file_dir, "r") as b:
	    y_dict = json.load(b)
	for biz in y_dict:
		category_value  = y_dict[biz].get("category",None)
		categories_set.add(category_value)
		
		biz_category = y_dict[biz].get("category","Without category")
		attributes_set = attributes_type.get(biz_category,set())
		if "attributes" in y_dict[biz].keys():
			attr_dict = y_dict[biz]["attributes"]
			if isinstance(attr_dict,dict):
				for key,value in attr_dict.items():
					attributes_set.add((key,value))
					attributes_type[biz_category] = attributes_set
		else:
			y_dict[biz]["attributes"] = None


# attributes_set_dict = {}
# for key, value in list(attributes_set):
#     attr_list = attributes_set_dict.get(key,[])
#     attr_list.append(value)
#     attributes_set_dict[key] = attr_list

for key,values in attributes_type.items():
	attributes_type[key] = list(values)

with open('attributes_final.json', "w") as c:
    json.dump(attributes_type,c)

for key in attributes_type.keys():
	f = open('attributes_'+key+".csv", 'w')
	w = csv.writer(f, delimiter=",",skipinitialspace=True)
	for key,value in attributes_type[key]:
		w.writerow([key,value])

	f4 = open('categories.csv', 'w')
	w4 = csv.writer(f4, delimiter=",")
	for key in sorted(list(attributes_type.keys())):
		w4.writerow([key])
	f4.close()

	# if "Yes" in values or "No" in values:
	# 	w.writerow([key])
	# else:
	# 	for value in values:
	# 		w.writerow([key,value])

f.close()

f1 = open('subcategories.csv', 'w')
w1 = csv.writer(f1, delimiter=",")
for category in list(categories_set):
	w1.writerow([category])

f1.close()

f2 = open('neighborhood.csv', 'w')
w2 = csv.writer(f2, delimiter=",")
for neighborhood in sorted(list(neighborhood_set)):
	w2.writerow([neighborhood])

f2.close()

f3 = open('attributes_1.csv', 'w')
w3 = csv.writer(f3, delimiter=",")

csvfile = open('attributes.csv', 'r')
info =csv.reader(csvfile,skipinitialspace = True)
for row in info:
	if len(row) == 1:
		w3.writerow(row)

f3.close()

f5 = open('attributes_2.csv', 'w')
w5 = csv.writer(f5, delimiter=",")

csvfile = open('attributes.csv', 'r')
info =csv.reader(csvfile,skipinitialspace = True)
for row in info:
	if len(row) != 1:
		for item in row:		
			w5.writerow([item])

f5.close()


with open("categories.json", "r") as b:
    Yelp_categories = json.load(b)

categories_dict = {}
count = 0
for cat in Yelp_categories:
	for parent in range(len(cat["parents"])):
		current_list = categories_dict.get(cat["parents"][parent],[])
		current_list.append(cat["title"])
		categories_dict[cat["parents"][parent]] = current_list

parent_dict = {"beautysvc":"Beauty","food":"Food","shopping":"Shopping",
			"fashion":"Fashion","arts":"Arts","restaurants":"Restaurants",
			"bars":"Bars","nightlife":"Nightlife","active":"Recreation"}

category_freq = {}
for parent,title_list in categories_dict.items():
	if parent in list(parent_dict.keys()):
		for title in title_list:
			if title in categories_set:
				current_list = category_freq.get(parent_dict[parent],[])
				current_list.append(title)
				category_freq[parent_dict[parent]] = current_list

with open('categories_final.json', "w") as c:
    json.dump(category_freq,c)


