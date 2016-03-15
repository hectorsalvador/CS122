# Cheap Chicago - Final project for CS122
# Carlos O. Grandet Caballero
# Hector Salvador Lopez

# ORIGINAL CODE, except when otherwise noted
# IMPORTANT: RUN THIS CODE WITH PYTHON 2.7
# The crawler was used to obtain establishments information from the
# Yelp website. It took advantage of the yelp search url structure:
# x = "http://www.yelp.com/search?start=0&sortby=rating&cflt=food&attrs=RestaurantsPriceRange2.1&l=p:IL:Chicago::Lakeview"
# To make an efficient search within the Yelp website of all the establishments
# that met the criteria that the user needed, then it scrapper the business info
# from the website and from the API. The crawler is inspired on PA2, it uses the
# Beautiful Soup library we saw in class, as well as two functions that were
# provided by the instructors in PA2. Finally, it uses a code provided by Yelp to
# connect to the API.

import argparse
from bs4 import BeautifulSoup
import cgi
import csv
import datetime
import json
import oauth2
import pprint
import Queue
import re
import requests
import sys
import urlparse
import urllib
import urllib2

def get_soup(url, url_set):
    '''
    Get the soup from an url and add the url to a set of previously visited
    websites.
    Input:
        url - a url from YELP domain
        url_set - a set of YELP urls
    Output
        a beautiful soup object
    '''
    html = urllib.urlopen(url).read()
    soup = BeautifulSoup(html,"html.parser")
    url_set.add(url) 
    return soup


def create_website(criteria):
    '''
    Creates the first website url to crawl based on neighborhood, type of 
        establishment, and price range 
    Inputs: 
        criteria, a dictionary with three keys indicating neighborhood, 
        type of establishment, and price range
    Output: 
        a website url 
    '''
    neighborhood = criteria["neighborhood"].split()
    establishment = criteria["establishment"]
    price_range = criteria["price_range"]
    basic_url = "http://www.yelp.com/search?"
    establishment_url = "sortby=rating&cflt={x}&attrs=Restaurants".format(x = \
        establishment)
    price_url = "PriceRange2.{x}&".format(x = price_range)
    neighborhood_url = "l=p:IL:Chicago::{x}".format(x = "_".join(neighborhood))
    final_url = basic_url + establishment_url + price_url + neighborhood_url
    return final_url


def add_links(tag, url_queue, url_set):
    '''
    Function to add all the links (href tag) to an url queue
    Inputs:
        tag, a BS4 tag object
        url_queue, a queue of url to visit
        url_set, a visited url set
    '''
    url = tag.get("href")
    url = remove_fragment(url)
    url = convert_if_relative_url("http://www.yelp.com/", url)

    #If the url has ?search in its uril structure, remove
    #this from the url. Add all links to the url queue. 
    if re.search("(.+)(\?search)", url) != None:
        url = re.search("(.+)(\?search)", url).group(1)  
    if url != None and url not in url_set: 
        url_queue.put(url)


def add_business_urls(soup, url_queue, url_set):
    '''
    Add all business found in an url
    Inputs:
        soup, a website BS4 soup object
        url_queue, a queue of url to visit
        url_set, a visited url set
    '''
    biz_tags = soup.find_all("a", class_ = "biz-name")
    if biz_tags == None:
        print("not a result page")
        return None
    for tag in biz_tags:
        add_links(tag, url_queue, url_set)


def add_additional_pages_urls(soup, url_queue, url_set):
    '''
    Add all result pages from a search engine.
    Inputs:
        soup, a website BS4 soup object
        url_queue, a queue of url to visit
        url_set, a visited url set
    '''
    result_tag = soup.find_all("a", class_ = \
        "available-number pagination-links_anchor")
    if result_tag == None:
        print("link not available")
        return None
    for tag in result_tag:
        add_links(tag, url_queue, url_set)

        
def get_biz_info(soup, url_set, attributes_set, max_review):
    '''
    Add all info from one business into a dictionary
    Inputs:
        soup, a website BS4 soup object
        url_set, a visited url set
        attributes_set, a set of attributes of a business (provided by YELP)
            (e.g. hipster, karaoke, romantic)
        max_review, a maximum amount of pages to obtain reviews from
    Outputs: 
        a dictionary with business info
    '''
    #Find the section in a Soup that has info from a business
    main_tag = soup.find("div", class_ = "biz-page-header-left")
    #If such section doest not exist, return None
    if main_tag == None:
        print("not a business page")
        return None

    biz_dict = {}
    #Get main attributes of business
    price = main_tag.find("span", class_ = "business-attribute price-range")
    if price == None:
        print("not price")
        return None
    else:
        biz_dict["price"] = price.text
    number_of_reviews = main_tag.find("span", itemprop = "reviewCount")
    if number_of_reviews == None:
        print("not reviews")
        return None
    else:
        biz_dict["number_of_reviews"] = number_of_reviews.text
    rating = main_tag.find("meta", itemprop = "ratingValue")
    if number_of_reviews == None:
        print("not rating")
        return None
    else:
        biz_dict["rating"] = rating.get("content")
    
    #Get opening and closing times
    hours_tag = soup.find("table", class_ = "table table-simple hours-table")
    time_dict = {}
    if hours_tag != None:
        for tag in hours_tag.find_all("tr"):
            day = tag.find("th").text
            hours_list = []
            for time in tag.find("td").find_all("span"):
                hours_list.append(time.text)
            time_dict[day] = hours_list
        biz_dict["times"] = time_dict
        
    #Get attributes
    attribute_tag = soup.find("div",class_ = "short-def-list")
    attributes_dict = {} 
    if attribute_tag != None:
        for tag in attribute_tag.find_all("dl"):
            attr_title = re.search("[A-Za-z0-9].+",tag.find("dt").text).group(0)
            attr_desc = re.search("[A-Za-z0-9].+",tag.find("dd").text).group(0)
            attributes_dict[attr_title] = attr_desc 
            attributes_set.add((attr_title, attr_desc))
        biz_dict["attributes"] = attributes_dict
    
    #Get reviews
    comment_dict = {}
    comment_url_queue = Queue.Queue()
    comment_url_set = set()

    #Crawl reviews pages, sometimes there were businesses with more than
    #one review page, in this case, we did a subcrawler that went into those 
    #pages and obtained information from them. 
    add_additional_pages_urls(soup,comment_url_queue,comment_url_set)
    soup_list = [soup]
    #We limitted the crawling to 2 review pages (up to 60 comments, to make
    #faster the crawling process). 
    while not comment_url_queue.empty() and len(comment_url_set) < max_review:
        current_url = comment_url_queue.get()+"&sort_by=date_desc"
        #Print this to determine if a business had more than 1 reviews page.
        print(current_url,"comment_website")
        current_soup = get_soup(current_url,comment_url_set)
        # add_additional_pages_urls(current_soup,comment_url_queue,comment_url_set)
        soup_list.append(current_soup)

    #Store selected information in a review dictionary
    number_comment = 0 
    for soup_item in soup_list:
        comment_tag = soup_item.find_all("div", class_ = "review-content")
        if comment_tag != None:
            for tag in comment_tag:
                description = tag.find("p", itemprop = "description").text
                rating = re.search("\d", tag.find("i").get("title")).group(0)
                date_list = tag.find("meta", itemprop = "datePublished"\
                    ).get("content").split("-")
                date_list = [int(val) for val in date_list]
                comment_dict[number_comment] = {"description": description, \
                "rating": rating, "date": date_list} 
                number_comment += 1
                
    biz_dict["comments"] = comment_dict
    
    return biz_dict


def run_model(criteria, num_pages_to_crawl,filename, attributes_set, max_review):
    '''
    Run a crawling model for a set of criteria and store relevant information 
        into filenames
    Inputs:
        criteria, dictionary with the type of establishment you are interested
            in looking for. (e.g. neighborhood, price, type of establishment)
        num_pages_to_crawl, int of maximum amount of pages to crawl
        filename, string with name of file where to store the dictionary
        attributes_set, a set of attributes for all the business in the
            model. (It is an input of the function because it is a set that all
            neighborhoods share).
        max_review, an int of the maximum number of pages to obtain reviews from
    '''
    # Create the first url to start the crawling
    original_url = create_website(criteria)
    url_set = set()
    url_queue = Queue.Queue()
    url_queue.put(original_url)

    establishments_dict = {}
    api_dict = {}
    while not url_queue.empty() and len(url_set) <= num_pages_to_crawl:
        current_url = url_queue.get()
        if current_url in url_set:
            continue
        print(current_url)
        soup = get_soup(current_url, url_set)
        biz_dict = get_biz_info(soup, url_set, attributes_set, max_review)
        if biz_dict != None:
            if re.search("(biz/)(.+)(\?+)", current_url) == None:
                biz_id = re.search("(biz/)(.+)(\?*)", current_url).group(2)
            else:
                biz_id = re.search("(biz/)(.+)(\?+)", current_url).group(2)
            print(biz_id)

            # Do exceptions to determine which was the problem with retrieving 
            # info from the API
            try:
                api_dict[biz_id] = get_business(biz_id)
            except:
                print("biz_id not valid")
            try:
                biz_dict["categories"] = api_dict[biz_id]["categories"]
            except:
                print("categories failed")
            try:    
                biz_dict["address"] = api_dict[biz_id]["location"]["address"]
            except:
                print("address failed")
            try:
                biz_dict["neighborhoods"] = \
                api_dict[biz_id]["location"]["neighborhoods"]
            except:
                print("neighborhoods failed")
            try:        
                biz_dict["latitude"] = \
                api_dict[biz_id]["location"]["coordinate"]["latitude"]
            except:
                print("latitude failed")
            try:
                biz_dict["longitude"] = \
                api_dict[biz_id]["location"]["coordinate"]["longitude"]
            except:
                print("longitude failed")

            #Open dictionary from neighborhood and add new business,
            #We update the json each time a business is added to save the
            #information and don't wait until the whole neighborhood has been
            #crawled. This is done in case the crawler gets stuck or our rights
            #revoked from YELP.
            try:
                with open(filename, "r") as b:
                    establishments_dict = json.load(b)
                    establishments_dict[biz_id] = biz_dict
                    
                with open(filename, "w") as c:
                    json.dump(establishments_dict,c, sort_keys=True)

            #If the dictionary file does not exist, create file. 
            except:
                with open(filename, "w") as c:
                    json.dump(establishments_dict,c)
                    establishments_dict[biz_id] = biz_dict

        #If a url is not a business page, obtain the bussiness and search urls 
        #from that page.
        else: 
            add_business_urls(soup, url_queue, url_set)
            add_additional_pages_urls(soup, url_queue, url_set)

####################################################################
# Author: CSS 122 PA2                                              #
# DIRECT COPY                                                      #
####################################################################
def is_absolute_url(url):
    '''
    Answer question: Is url an absolute URL?
    '''
    if len(url) == 0:
        return False
    return len(urlparse.urlparse(url).netloc) != 0


def remove_fragment(url):
    '''remove the fragment from a url'''
    (url, frag) = urlparse.urldefrag(url)
    return url


def convert_if_relative_url(current_url, new_url):
    '''
    Attempt to determine whether new_url is a relative URL and if so,
    use current_url to determine the path and create a new absolute
    URL.  Will add the protocol, if that is all that is missing.

    Inputs:
        current_url: absolute URL
        new_url: 

    Outputs:
        new absolute URL or None, if cannot determine that
        new_url is a relative URL.

    Examples:
        convert_if_relative_url("http://cs.uchicago.edu", "pa/pa1.html") yields 
            'http://cs.uchicago.edu/pa/pa.html'

        convert_if_relative_url("http://cs.uchicago.edu", "foo.edu/pa.html") 
            yields 'http://foo.edu/pa.html'
    '''
    if len(new_url) == 0 or not is_absolute_url(current_url):
        return None

    if is_absolute_url(new_url):
        return new_url

    parsed_url = urlparse.urlparse(new_url)
    path_parts = parsed_url.path.split("/")

    if len(path_parts) == 0:
        return None

    ext = path_parts[0][-4:]
    if ext in [".edu", ".org", ".com", ".net"]:
        return parsed_url.scheme + new_url
    elif new_url[:3] == "www":
        return parsed_url.scheme + new_path
    else:
        return urlparse.urljoin(current_url, new_url)

####################################################################
# Author: Ken Mitton (Yelp)                                        #
# kmitton@yelp.com                                                 #
# https://github.com/Yelp/yelp-api/blob/master/v2/python/sample.py #
# DIRECT COPY                                                      #
####################################################################

API_HOST = 'api.yelp.com'
SEARCH_LIMIT = 20
BUSINESS_PATH = '/v2/business/'

CONSUMER_KEY = 'dStcfiGFCoZkOlva9XeZtA'
CONSUMER_SECRET = 'WoJ9LxTFCVgdYFq6yn3GAlLRRXE'
TOKEN = 'VnMH3YjeyYcvV4mhXVzfcJhOwRNgaBFX'
TOKEN_SECRET = 'boGGX7K0aX2gcY39kF3uAwuEdu0'

def request(host, path, url_params = None):
    """Prepares OAuth authentication and sends the request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        urllib2.HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = 'https://{0}{1}?'.format(host, urllib.quote(path.encode('utf8')))

    consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    oauth_request = oauth2.Request(
        method = "GET", url = url, parameters = url_params)

    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': TOKEN,
            'oauth_consumer_key': CONSUMER_KEY
        }
    )
    token = oauth2.Token(TOKEN, TOKEN_SECRET)
    oauth_request.sign_request(
        oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()

    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()

    return response

def get_business(business_id):
    """Query the Business API by a business ID.
    Args:
        business_id (str): The ID of the business to query.
    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path)

################################
################################

if __name__=="__main__":

    INITIAL_WEBSITE = "http://www.yelp.com/"
    TYPE_ESTABLISHMENT =  ["food", "restaurants", "beautysvc", "active", 
    "arts", "nightlife", "shopping"]
    NEIGHBORHOODS = ["Englewood", "Forest Glen", "Fulton Market", "Gage Park", 
    'Galewood', "Garfield Ridge", "Gold Coast", 'Goose Island', 
    'Grand Boulevard', 'Greater Grand Crossing', "Greektown", "Hegewisch", 
    "Hermosa", "Humboldt Park", "Irving Park", "Jefferson Park", 
    "Jeffery Manor", "Kenwood", "Lakeview", "Lawndale", "Lincoln Park", 
    "Lincoln Square", "Little Village", "Marquette Park", "McKinley Park",
    "Montclare", "Morgan Park", "Mount Greenwood", "Near North Side",
    "Near Southside", "Near West Side", "New City", "Noble Square",
    "North Center", "North Park", "Norwood Park", "O'Hare", "Oakland",
    "Old Town", "Portage Park", "Printer's Row", "Pullman", "Ravenswood", 
    "River East", "Pilsen","Hyde Park","South Loop","Wicker Park", 
    "Albany Park", "The Loop", "Andersonville", "Archer Heights","Ashburn", 
    "Auburn Gresham", "Austin", "Avalon Park", "Avondale", "Back of the Yards",
    "Magnificent Mile","River North","Logan Square","Belmont Central",
    "Beverly", "Brainerd", "Bridgeport", "Brighton Park", "Bronzeville", 
    "Bucktown", "Burnside", "Cabrini-Green", "Calumet Heights", "Canaryville",
    "Chatham", "Chicago Lawn", "Chinatown", "Clearing", "Cragin", "DePaul", 
    "Douglas", "Dunning", "East Garfield Park","East Side", "Edgewater",
    "Edison Park",]
    PRICERANGE = [1, 2]
    NUMBER_OF_WEBSITES = 100
    MAX_REVIEW = 2

    criteria_dict = {}
    number_criteria = 0
    for neighborhood in NEIGHBORHOODS:
        for establishment in TYPE_ESTABLISHMENT:
            for price in PRICERANGE:
                criteria_dict[number_criteria] = {"neighborhood": neighborhood,\
                    "establishment": establishment, "price_range": price}
                number_criteria += 1
    
    attributes_set = set()
    for criteria in criteria_dict.values():
        print("######{criteria}#######".format(criteria = criteria))
        filename = "{x}_dict.json".format(x = criteria["neighborhood"])
        run_model(criteria, NUMBER_OF_WEBSITES, filename, attributes_set, \
            MAX_REVIEW)

    attributes_set_dict = {}
    for key, value in list(attributes_set):
        attr_list = attributes_set_dict.get(key,[])
        attr_list.append(value)
        attributes_set_dict[key] = attr_list
    
    with open('attributes_dict.json', "w") as c:
        json.dump(attributes_set_dict,c)
 
