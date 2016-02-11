# CS122: Course Search Engine Part 1
#
# Carlos O. Grandet Caballero
# Hector Salvador Lopez

import re
import util
from bs4 import BeautifulSoup
import queue
import json
import sys
import csv
import urllib
import requests
import datetime


INITIAL_WEBSITE = "http://www.yelp.com/"

TYPE_ESTABLISHMENT = ["Active Life", "Arts & Entertainment", "Automotive", "Beauty & Spas", "Education", 
                    "Event Planning & Services","Financial Services","Food","Health & Medical", "Home Services",
                    "Hotels & Travel","Local Flavor","Local Services","Mass Media","Nightlife","Pets",
                    "Professional Services", "Public Services & Government", "Real Estate", 
                    "Religious Organizations","Restaurants","Shopping"]
NEIGHBORHOOD = []

criteria = {"neighborhood":"Hyde Park","establishment":"food","price_range":"1"}

biz = "http://www.yelp.com/biz/robust-coffee-lounge-chicago"
url_set = set()

def get_soup(url, url_set):
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html,"html5lib")
    url_set.add(url) 

    return soup

def create_website(criteria):
    '''
    Create the first website to crawl info based on characteristics 

    Output: a website url 
    '''
    neighborhood = criteria["neighborhood"].split()
    establishment = criteria["establishment"]
    price_range = criteria["price_range"]
    basic_url = "http://www.yelp.com/search?"
    neighborhood_url = "find_loc={x},+Chicago,+IL&start=0&".format(x = "+".join(neighborhood))
    establishment_url = "sortby=rating&cflt={x}&attrs=Restaurants".format(x = establishment)
    price_url = "PriceRange2.{x}".format(x = price_range)
    final_url = basic_url + neighborhood_url + establishment_url + price_url
    return final_url

def add_business_urls(soup,url_queue,url_set,list_biz):
    biz_tags = soup.find_all("a",class_= "biz-name")
    for tag in biz_tags:
        biz_url = tag.get("href")
        biz_name = re.search('(?![biz])[A-Za-z0-9-]+',biz_url)
        list_biz.append(biz_name.group(0))
        biz_url = util.remove_fragment(biz_url)
        biz_url = util.convert_if_relative_url("http://www.yelp.com/", biz_url)
        if biz_url != None and biz_url not in url_set: 
            url_queue.put(biz_url)

    return list_biz

def get_all_business_urls(criteria):
    original_url = create_website(criteria)
    url_set = set()
    original_soup = get_soup(original_url, url_set)
    original_soup.find_all("a", class_ = "available-number pagination-links_anchor")


def get_biz_info(url,url_set):
    soup = get_soup(url,url_set)
    main_tag = soup.find("div", class_= "biz-page-header-left")
    attribute_tag = soup.find("div",class_ = "short-def-list").find_all("dl")
    biz_dict = {}
    for tag in attribute_tag:
        attr_title = re.search("[A-Za-z].+",tag.find("dt").text).group(0)
        attr_desc = re.search("[A-Za-z].+",tag.find("dd").text).group(0)
        biz_dict[attr_title] = attr_desc 
    comment_tag = soup.find_all("div", class_ = "review-content")
    comment_dict = {}
    for i, tag in enumerate(comment_tag):
        description = tag.find("p", itemprop = "description").text
        rating = re.search("\d",tag.find("i").get("title")).group(0)
        date_list = tag.find("meta", itemprop = "datePublished").get("content").split("-")
        date_list = [int(i) for i in date_list]
        date = datetime.date(date_list[0],date_list[1],date_list[2])
        comment_dict[i] = {"description":description,"rating":rating,"date":date}
    biz_dict["comments"] = comment_dict

    return biz_dict

biz_dict = get_biz_info(biz,url_set)
json.dumps(biz_dict)

def add_urls_from_website(object_soup, url_queue, parent_url, url_set):
    '''
    get all the urls linked to a website and add them to a 
    queue of websites to follow. 

    Inputs:
        object_soup : a Beautiful Soup object
        url_queue : a queue of websites to visit 
        parent_url: the parent url from which you are crawling
        url_set: a set of visited urls 

    Outputs: 
        None. Adds urls to the provided url_queue
    '''
    a_tags = object_soup.find_all("a","")
    for tag in a_tags:
        tag_url = tag.get("href", "fake_website")
        if not util.is_absolute_url(tag_url):
            tag_url = util.remove_fragment(tag_url)
            tag_url = util.convert_if_relative_url(parent_url, tag_url)
        
        if tag_url != None and tag_url not in url_set and \
            util.is_url_ok_to_follow(tag_url, LIMITING_DOMAIN): 
            url_queue.put(tag_url)


def go(num_pages_to_crawl, course_map_filename, index_filename):
    '''
    Crawl the college catalog and generates a CSV file with an index.

    Inputs:
        num_pages_to_crawl: an integer, the number of pages to process during 
            the crawl
        course_map_filename: a string with the name of a JSON file that contains
            the mapping course codes to course identifiers
        index_filename: a string with the name for the CSV of the index

    Outputs: 
        CSV file of the index
    '''

    course_index = crawl_website(STARTING_URL, LIMITING_DOMAIN, num_pages_to_crawl)
    gen_csv_file(course_index, course_map_filename, index_filename)

    return course_index


def crawl_website(initial_url, limiting_domain, num_pages_to_crawl):
    '''
    Inputs:
        initial_url: a string with the initial url to follow
        limiting_domain: a string with the domain where the crawling should
            be limited to
        num_pages_to_crawl: an integer to restrict the maximum number of
            visited pages

    Output:
        course_index: a dictionary with the course id's of the College 
            catalog as keys and their descriptions as items
    '''

    url_queue = queue.Queue() 
    url_visits = set() 
    course_index = {}

    url_queue.put(initial_url)
    while not url_queue.empty() and len(url_visits) <= num_pages_to_crawl:
        website = url_queue.get()
        if website not in url_visits:
            url_visits.add(website)
            website_soup = get_website_soup(website, url_visits)
            if website_soup == None:
                pass
            else:
                add_urls_from_website(website_soup, url_queue, website, url_visits)
                gen_course_dictionary(website_soup, course_index)

    return course_index


def get_website_soup(url, url_set): 
    '''
    get website url as a beautiful soup object

    Inputs:
        url: string representing absolute url of a website 
        url_set: a set with the urls that have already been visited

    Outputs: 
        HTML beautiful soup object
    '''
    if len(url) == 0:
        print("url not absolute")
        return None

    else:   
        request_attempts = 0 
        # Try 3 times to get information from a site 
        while request_attempts <= 3:
            url_object = util.get_request(url)
            if url_object == None:
                request_attempts += 1
            elif url_object == None and request_attemtps == 3:
                print("request failed")
                return url_object

            #Read object and get Beautiful Soup object
            else: 
                object_text = util.read_request(url_object)
                object_url = util.get_request_url(url_object)
                url_set.add(object_url) 
                object_soup = bs4.BeautifulSoup(object_text, "html5lib")
                return object_soup


def add_urls_from_website(object_soup, url_queue, parent_url, url_set):
    '''
    get all the urls linked to a website and add them to a 
    queue of websites to follow. 

    Inputs:
        object_soup : a Beautiful Soup object
        url_queue : a queue of websites to visit 
        parent_url: the parent url from which you are crawling
        url_set: a set of visited urls 

    Outputs: 
        None. Adds urls to the provided url_queue
    '''
    a_tags = object_soup.find_all("a")
    for tag in a_tags:
        tag_url = tag.get("href", "fake_website")
        if not util.is_absolute_url(tag_url):
            tag_url = util.remove_fragment(tag_url)
            tag_url = util.convert_if_relative_url(parent_url, tag_url)
        
        if tag_url != None and tag_url not in url_set and \
            util.is_url_ok_to_follow(tag_url, LIMITING_DOMAIN): 
            url_queue.put(tag_url)


def gen_course_dictionary(object_soup, course_index):
    '''
    get the title of a course and add it as a key to the dictionary
    and adds the course description as value

    Inputs:
        object_soup : a Beautiful Soup object
        course_index : a dictionary relating a course with words  

    Outputs: 
        None. Updates the provided dictionary 
    '''

    div_tags = object_soup.find_all("div", class_ = "courseblock main")
    if len(div_tags) != 0:
        for tag in div_tags:
            
            # Get the course title and add it as a key
            title_tags = tag.find("p", class_ = "courseblocktitle")
            title_string = title_tags.text 
            title_string.replace("&#160;"," ")
            course_id = re.search("\w* [0-9]*", title_string.replace("\xa0", \
                " ")).group()
            course_index[course_id] = course_index.get(course_id, [])

            # Get the words of the course title and description and add each as
            # a value in a list
            course_title_words = re.findall('[a-zA-Z][a-zA-Z0-9]+', title_string)
            desc_tags = tag.find("p", class_ = "courseblockdesc")
            desc_string = desc_tags.text
            desc_words = re.findall("[a-zA-Z][a-zA-Z0-9]+", desc_string)
            list_words = desc_words + course_title_words
            
            list_sequences = util.find_sequence(tag)
            if len(list_sequences) != 0:
                for seq in list_sequences:
                    stitle_tags = seq.find("p", class_ = "courseblocktitle")
                    stitle_string = stitle_tags.text 
                    stitle_string.replace("&#160;", " ")
                    scourse_id = re.search("\w* [0-9]*", \
                        stitle_string.replace("\xa0", " ")).group()
                    course_index[scourse_id] = course_index.get(scourse_id, [])
                    sdesc_tags = seq.find("p", class_ = "courseblockdesc")
                    sdesc_string = sdesc_tags.text
                    slist_words = re.findall("[a-zA-Z][a-zA-Z0-9]+", sdesc_string)
                    final_list_words = slist_words + list_words
                    for word in final_list_words:
                        if word.lower() not in INDEX_IGNORE and word.lower() \
                        not in course_index[scourse_id]:
                            course_index.get(scourse_id).append(word.lower()) 
            else:          
                for word in list_words:
                    if word.lower() not in INDEX_IGNORE and word.lower() \
                    not in course_index[course_id]:
                        course_index.get(course_id).append(word.lower()) 
            
    

def gen_csv_file(course_index, course_map_filename,index_filename):
    '''
    This function generates a CSV file with course ID and the words
    associated to that course ID

    Inputs:
        course_index: a dictionary linking courses to words
        course_map_filename: a JSON file
        index_filename: the name of the CSV file 

    Outputs:
        A CSV file
    '''

    with open(course_map_filename) as map_filename:   
        json_data = json.load(map_filename)

    with open(index_filename, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter = '|')
        for course_title in list(course_index.keys()):
            for word in course_index[course_title]:
                course_code = json_data[course_title] 
                writer.writerow([course_code, word])

    return index_filename


# if __name__ == "__main__":
#     usage = "python3 crawl.py <number of pages to crawl>"
#     args_len = len(sys.argv)
#     course_map_filename = "course_map.json"
#     index_filename = "catalog_index.csv"
#     if args_len == 1:
#         num_pages_to_crawl = 1000
#     elif args_len == 2:
#         try:
#             num_pages_to_crawl = int(sys.argv[1])
#         except ValueError:
#             print(usage)
#             sys.exit(0)
#     else:
#         print(usage)    
#         sys.exit(0)

#     go(num_pages_to_crawl, course_map_filename, index_filename)

