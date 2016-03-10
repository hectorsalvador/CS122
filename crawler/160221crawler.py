# v 0.1 for Python 2.7
# Carlos O. Grandet Caballero
# Hector Salvador Lopez

import re
from bs4 import BeautifulSoup
import Queue
import json
import sys
import csv
import argparse
import pprint
import urlparse
import urllib
import urllib2
import requests
import datetime
import requests
import oauth2
import cgi


def get_soup(url, url_set):
    html = urllib.urlopen(url).read()
    soup = BeautifulSoup(html,"html.parser")
    url_set.add(url) 
    return soup

    # proxy = urllib2.ProxyHandler( {'http': url} )
    # # Create an URL opener utilizing proxy
    # opener = urllib2.build_opener( proxy )
    # urllib2.install_opener( opener )
    # request = urllib2.Request( url )
    # response = urllib.urlopen( request )

    # # Aquire data from URL
    # html = response.read()
    # return request
    # proxies = {
    # 'http': 'http://107.190.165.47'}
    # r = requests.get(url, proxies = proxies)
    # r.text.encode('iso-8859-1')
    # object_soup = bs4.BeautifulSoup(object_text, "html5lib")

    # return object_soup

def create_website(criteria):
    '''
    Creates the first website url to crawl based on neighborhood, type of 
        establishment, and price range 
    Input: criteria - a dictionary with three keys indicating neighborhood, 
        type of establishment, and price range
    Output: a website url 
    '''
    x = "http://www.yelp.com/search?start=0&sortby=rating&cflt=food&attrs=RestaurantsPriceRange2.1&l=p:IL:Chicago::Lakeview"
    neighborhood = criteria["neighborhood"].split()
    establishment = criteria["establishment"]
    price_range = criteria["price_range"]
    basic_url = "http://www.yelp.com/search?"
    establishment_url = "sortby=rating&cflt={x}&attrs=Restaurants".format(x = establishment)
    price_url = "PriceRange2.{x}&".format(x = price_range)
    neighborhood_url = "l=p:IL:Chicago::{x}".format(x = "_".join(neighborhood))
    final_url = basic_url + establishment_url + price_url + neighborhood_url
    return final_url

def add_links(tag, url_queue, url_set):
    url = tag.get("href")
    url = remove_fragment(url)
    url = convert_if_relative_url("http://www.yelp.com/", url)
    # scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
    # url = scheme+"://"+netloc+path
    if re.search("(.+)(\?search)", url) != None:
        url = re.search("(.+)(\?search)", url).group(1)  
    if url != None and url not in url_set: 
        url_queue.put(url)

def add_business_urls(soup, url_queue, url_set):
    biz_tags = soup.find_all("a", class_= "biz-name")
    if biz_tags == None:
        print("not a result page")
        return None
    for tag in biz_tags:
        # biz_name = re.search('(?![biz])[A-Za-z0-9-]+',biz_url)
        # list_biz.append(biz_name.group(0))
        add_links(tag, url_queue, url_set)

def add_additional_pages_urls(soup, url_queue, url_set):
    result_tag = soup.find_all("a", class_ = "available-number pagination-links_anchor")
    if result_tag == None:
        print("link not available")
        return None
    for tag in result_tag:
        add_links(tag, url_queue, url_set)

    # return list_biz

def get_biz_info(soup, url_set, attributes_set):
    main_tag = soup.find("div", class_= "biz-page-header-left")
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
                #hours_list.append(datetime.datetime.strptime(time.text, "%I:%M %p")) Cambio para Json file
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
    
    #Get comments 
    comment_dict = {}
    comment_url_queue = Queue.Queue()
    comment_url_set = set()
    #Crawl comments pages
    add_additional_pages_urls(soup,comment_url_queue,comment_url_set)
    soup_list = [soup]
    while not comment_url_queue.empty() and len(comment_url_set) < 2:
        current_url = comment_url_queue.get()+"&sort_by=date_desc"
        print(current_url,"comment_website")
        current_soup = get_soup(current_url,comment_url_set)
        # add_additional_pages_urls(current_soup,comment_url_queue,comment_url_set)
        soup_list.append(current_soup)
        
    
    number_comment = 0 
    for soup_item in soup_list:
        comment_tag = soup_item.find_all("div", class_ = "review-content")
        if comment_tag != None:
            for tag in comment_tag:
                description = tag.find("p", itemprop = "description").text
                rating = re.search("\d", tag.find("i").get("title")).group(0)
                date_list = tag.find("meta", itemprop = "datePublished").get("content").split("-")
                date_list = [int(val) for val in date_list]
                # date = datetime.date(date_list[0],date_list[1],date_list[2])
                comment_dict[number_comment] = {"description" : description, "rating" : rating, \
                "date" : date_list} #Cambio para hacerlo JSON
                number_comment += 1


    biz_dict["comments"] = comment_dict
    
    return biz_dict


def run_model(criteria, num_pages_to_crawl,filename, attributes_set):
    original_url = create_website(criteria)
    url_set = set()
    url_queue = Queue.Queue()
    url_queue.put(original_url)

    establishments_list = []
    establishments_dict = {}
    api_dict = {}
    
    
    while not url_queue.empty() and len(url_set) <= num_pages_to_crawl:
        current_url = url_queue.get()
        if current_url in url_set:
            continue

        print(current_url)
        print(len(url_set))
        soup = get_soup(current_url, url_set)
        biz_dict = get_biz_info(soup, url_set, attributes_set)
        #biz_id = re.search("(biz/)(.+)(\?*)", current_url).group(2)
        if biz_dict != None:
        #if biz_dict != None and establishments_dict[biz_id]:
            if re.search("(biz/)(.+)(\?+)", current_url) == None:
                biz_id = re.search("(biz/)(.+)(\?*)", current_url).group(2)
            else:
                biz_id = re.search("(biz/)(.+)(\?+)", current_url).group(2)
            print(biz_id)
            
            try:
                api_dict[biz_id] = get_business(biz_id)
            except:
                print("API failed")
            try:
                biz_dict["categories"] = api_dict[biz_id]["categories"]
            except:
                print("categories failed")
            try:    
                biz_dict["address"] = api_dict[biz_id]["location"]["address"]
            except:
                print("address failed")
            try:
                biz_dict["neighborhoods"] = api_dict[biz_id]["location"]["neighborhoods"]
            except:
                print("neighborhoods failed")
            try:        
                biz_dict["latitude"] = api_dict[biz_id]["location"]["coordinate"]["latitude"]
            except:
                print("latitude failed")
            try:
                biz_dict["longitude"] = api_dict[biz_id]["location"]["coordinate"]["longitude"]
            except:
                print("longitude failed")

            try:
                with open(filename, "r") as b:
                    establishments_dict = json.load(b)
                    establishments_dict[biz_id] = biz_dict
                with open(filename, "w") as c:
                    json.dump(establishments_dict,c, sort_keys=True)

            except:
                with open(filename, "w") as c:
                    json.dump(establishments_dict,c)
                    establishments_dict[biz_id] = biz_dict
            
        else: 
            add_business_urls(soup, url_queue, url_set)
            add_additional_pages_urls(soup, url_queue, url_set)


def is_absolute_url(url):
    '''
    Is url an absolute URL?
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

        convert_if_relative_url("http://cs.uchicago.edu", "foo.edu/pa.html") yields
            'http://foo.edu/pa.html'
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

##################################
### Author: Ken Mitton (Yelp)   ##
### kmitton@yelp.com            ##
### https://github.com/Yelp/yelp-api/blob/master/v2/python/sample.py
##################################

API_HOST = 'api.yelp.com'
SEARCH_LIMIT = 20
BUSINESS_PATH = '/v2/business/'

CONSUMER_KEY = 'dStcfiGFCoZkOlva9XeZtA'
CONSUMER_SECRET = 'WoJ9LxTFCVgdYFq6yn3GAlLRRXE'
TOKEN = 'VnMH3YjeyYcvV4mhXVzfcJhOwRNgaBFX'
TOKEN_SECRET = 'boGGX7K0aX2gcY39kF3uAwuEdu0'

def request(host, path, url_params=None):
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
        method="GET", url=url, parameters=url_params)

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

    # print u'Querying {0} ...'.format(url)

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
    TYPE_ESTABLISHMENT =  ["food","restaurants","beautysvc","active","arts","nightlife","shopping"]
<<<<<<< HEAD
    NEIGHBORHOODS = [ "Uptown", "Washington Heights", "Washington Park","West Elsdon", "West Englewood",
               "West Garfield Park", "West Lawn","West Loop", "West Pullman", "West Rogers Park", "West Town",
               "Woodlawn", "Wrigleyville"]
    MISSING = ["Lincoln Park", "Lincoln Square", "Little Village"]
    DONE_NEIGHBORHOODS = ["Pilsen","Hyde Park","South Loop","Wicker Park","Albany Park", "The Loop",
=======
    NEIGHBORHOODS = ["Lincoln Square", "Little Village"]
    MISSING = ["Marquette Park", "McKinley Park",
"Montclare", "Morgan Park", "Mount Greenwood", "Near North Side",
"Near Southside", "Near West Side", "New City", "Noble Square",
"North Center", "North Park", "Norwood Park", "O'Hare", "Oakland",
"Old Town", "Portage Park", "Printer's Row", "Pullman",
"Ravenswood", "River East"]
    DONE_NEIGHBORHOODS = ["Garfield Ridge","Lincoln Park","Gold Coast", 'Goose Island', 'Grand Boulevard',
                          'Greater Grand Crossing',"Greektown", "Hegewisch",
                          "Hermosa", "Humboldt Park", "Irving Park",
                          "Jefferson Park", "Jeffery Manor", "Kenwood",
                          "Lakeview","Lawndale", "Englewood","Forest Glen",
                          "Fulton Market", "Gage Park", 'Galewood',
                        "Pilsen","Hyde Park","South Loop","Wicker Park","Albany Park", "The Loop",
>>>>>>> origin/master
                        "Andersonville", "Archer Heights","Ashburn", "Auburn Gresham",
                        "Austin", "Avalon Park", "Avondale", "Back of the Yards",
                        "Magnificent Mile","River North","Logan Square","Belmont Central",
                        "Beverly", "Brainerd",
                        "Bridgeport", "Brighton Park", "Bronzeville", "Bucktown", "Burnside",
                        "Cabrini-Green", "Calumet Heights", "Canaryville", "Chatham", "Chicago Lawn",
                        "Chinatown", "Clearing", "Cragin", "DePaul", "Douglas", "Dunning",
                        "East Garfield Park","East Side", "Edgewater","Edison Park", 1,
                        "Englewood","Forest Glen", "Fulton Market", "Gage Park", 'Galewood', "Garfield Ridge",
                        "Gold Coast", 'Goose Island', 'Grand Boulevard', 'Greater Grand Crossing',
                        "Greektown", "Hegewisch", "Hermosa", "Humboldt Park", 
                        "Irving Park", "Jefferson Park", "Jeffery Manor", "Kenwood", "Lakeview",
                        "Lawndale", "Lincoln Park", "Lincoln Square", "Little Village",1,
                          "Marquette Park","McKinley Park",
                        "Montclare", "Morgan Park", "Mount Greenwood", "Near North Side",
                        "Near Southside", "Near West Side", "New City", "Noble Square",
                        "North Center", "North Park", "Norwood Park", "O'Hare", "Oakland",
                        "Old Town", "Portage Park", "Printer's Row", "Pullman",
                        "Ravenswood", "River East","River West", "Riverdale", "Rogers Park",
                        "Roscoe Village","Roseland", "Sauganash", "Scottsdale",
                        "South Chicago", "South Deering","South Shore","Streeterville",
                          "Tri-Taylor", "Ukrainian Village", "University Village",]
    PRICERANGE = [1,2]
    NUMBER_OF_WEBSITES = 50



    criteria_dict = {}
    number_criteria = 0
    for neighborhood in NEIGHBORHOODS:
        for establishment in TYPE_ESTABLISHMENT:
            for price in PRICERANGE:
                criteria_dict[number_criteria] = {"neighborhood": neighborhood, "establishment": establishment, "price_range": price}
                number_criteria += 1
    
    #Cuando falla activar este codigo para empezar desde el x diccionario
    # list_visited = range(40)
    # for i in list_visited:
    #     criteria_dict.pop(i, None)

    attributes_set = set()
    for criteria in criteria_dict.values():
        print("######{criteria}#######".format(criteria = criteria))
        filename = "{x}_dict.json".format(x = criteria["neighborhood"])
        run_model(criteria, NUMBER_OF_WEBSITES, filename, attributes_set)

    attributes_set_dict = {}
    for key, value in list(attributes_set):
        attr_list = attributes_set_dict.get(key,[])
        attr_list.append(value)
        attributes_set_dict[key] = attr_list
    
    with open('attributes_dict.json', "w") as c:
        json.dump(attributes_set_dict,c)
 

# #Museums not included
# #Limits to business 50
# #Do not consider business without price, comments or rating


# with open("East Side_dict.json", "r") as b:
#     y = json.load(b)

# ["Andersonville", "Archer Heights",
# "Ashburn", "Auburn Gresham", "Austin", "Avalon Park", "Avondale", 
# Back of the Yards, Belmont Central, Beverly, Brainerd,
# Bridgeport, Brighton Park, Bronzeville, Bucktown, Burnside,
# Cabrini-Green, Calumet Heights, Canaryville, Chatham, Chicago Lawn,
# Chinatown, Clearing, Cragin, DePaul, Douglas, Dunning,
# East Garfield Park, East Side, Edgewater, //Edison Park, Englewood,
# Forest Glen, Fulton Market, Gage Park, Galewood, Garfield Ridge,
# Gold Coast, Goose Island, Grand Boulevard, Greater Grand Crossing,
# Greektown, Hegewisch, Hermosa, Humboldt Park, 
# Irving Park, Jefferson Park, Jeffery Manor, Kenwood, Lakeview,
# Lawndale, Lincoln Park, Lincoln Square, Little Village,
# Logan Square, Magnificent Mile, Marquette Park, McKinley Park,
# Montclare, Morgan Park, Mount Greenwood, Near North Side,
# Near Southside, Near West Side, New City, Noble Square,
# North Center, North Park, Norwood Park, O'Hare, Oakland,
# Old Town, Portage Park, Printer's Row, Pullman,
# Ravenswood, River East, River West, Riverdale,
# Rogers Park, Roscoe Village, Roseland, Sauganash, Scottsdale,
# South Chicago, South Deering, South Shore,
# Streeterville, Tri-Taylor, Ukrainian Village,
# University Village, Uptown, Washington Heights, Washington Park,
# West Elsdon, West Englewood, West Garfield Park, West Lawn,
# West Loop, West Pullman, West Rogers Park, West Town,
# Woodlawn, Wrigleyville]]
