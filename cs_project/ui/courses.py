### CS122 W16: Course search engine: search
###
### Carlos Grandet-Caballero
### Hector Salvador Lopez

from math import radians, cos, sin, asin, sqrt
import sqlite3
import json
import re
import os


# Use this filename for the database
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'course-info.db')
path = '/home/student/cs122-win-16-cgrandet-hectorsalvador/cs_project/ui/neigborhoods'
# filename = "East Side_dict.json"
# with open(os.path.join(path, filename), "r") as b:
#         neigh = json.load(b)

def find_business(args_from_ui):
    neigh_name = args_from_ui["neigh"]
    filename = neigh_name+"_dict.json"
    with open(os.path.join(path, filename), "r") as b:
        neigh = json.load(b)
    header = ["business","address"]
    results = []
    for biz in neigh:
        if re.search("([A-Za-z-]+)-chicago",biz) == None:
            name = biz
        else:
            name = re.search("([A-Za-z-]+)-chicago",biz).group(1)
        address = "NA"
        if "address" in neigh[biz].keys():
            try:
                address = neigh[biz]["address"][0]
            except:
                None
        biz_list = [name,address]
        results.append(biz_list)

    # results = [["carlos", "grandet"],["carlos","castillo"]]
    return (header,results)


def find_courses(args_from_ui):
    '''
    Takes a dictionary containing search criteria and returns courses
    that match the criteria.  The dictionary will contain some of the
    following fields:

      - dept a string
      - day is array with variable number of elements  
           -> ["'MWF'", "'TR'", etc.]
      - time_start is an integer in the range 0-2359
      - time_end is an integer an integer in the range 0-2359
      - enroll is an integer
      - walking_time is an integer
      - building ia string
      - terms is a string: "quantum plato"]

    Returns a pair: list of attribute names in order and a list
    containing query results.
    '''

    if len(args_from_ui) == 0:
        table = ([],[])
    else:
        connection = sqlite3.connect(DATABASE_FILENAME)
        if 'building' in args_from_ui:
            connection.create_function("time_between", 4, compute_time_between)
        c = connection.cursor()
        query = create_query_string(args_from_ui)
        args = get_arguments(args_from_ui)
        table = format_database(query, args, c)

    return table

def create_query_string(args_from_ui):
    '''
    Takes a dictionary containing search criteria and returns a string that
    represents a SQL query code. Works specifically for the 'course-info.db'
    database

    Inputs
        args_from_ui: a dictionary

    Outputs
        query: a string
    '''
    KEYS_1 = {'day', 'time_start', 'time_end', 'walking_time', 'building'}
    KEYS_2 = {'walking_time', 'building'}
    KEYS_3 = {'enroll_lower', 'enroll_upper'}
    KEYS_4 = {'terms', 'dept'}
    args_keys = set(args_from_ui.keys())
    query = ''

    #SELECT part of the query
    query += 'SELECT c.dept AS "Department", c.course_num AS "Course number", '
    query_l = []
    if len(args_keys.intersection(KEYS_1)) != 0:
        query_l.append('s.section_num AS "Section", m.day AS "Day", m.time_start \
        AS "Time start", m.time_end AS "Time end" ')
    if len(args_keys.intersection(KEYS_2)) != 0:
        query_l.append('s.building_code AS "Building" ') 
    if len(args_keys.intersection(KEYS_3)) != 0:
        query_l.append('s.enrollment AS "Max enrollment" ')
    if len(args_keys.intersection(KEYS_4)) != 0:
        query_l.append('c.title AS "Title" ')
    query += ', '.join(query_l)
    
    #FROM part of the query
    query += ' FROM courses AS c '
    if len(args_keys.intersection({'building', 'enroll_lower',\
        'enroll_upper', 'day', 'time_start', 'time_end', 'walking_time',\
        'building'})) != 0:
        query += 'JOIN meeting_patterns AS m JOIN sections AS s\
        ON (c.course_id = s.course_id AND \
        s.meeting_pattern_id = m.meeting_pattern_id)'
    
    #WHERE part of the query
    query += ' WHERE '
    query_l = []
    if 'dept' in args_keys:
        query_l.append('c.dept = ?')
    if 'day' in args_keys:
        num_combos_2_match = len(args_from_ui['day'])
        squery = ''
        squery += 's.meeting_pattern_id IN \
            (SELECT meeting_pattern_id \
            FROM meeting_patterns \
            WHERE day IN (' + ', '.join(["?"] * num_combos_2_match) + '))'
        query_l.append(squery)
    if 'time_start' in args_keys:
        query_l.append('m.time_start >= ?')
    if 'time_end' in args_keys:
        query_l.append('m.time_end <= ?')
    if 'walking_time' in args_keys:
        squery = ''
        squery += 's.building_code IN \
            (SELECT building_code \
            FROM (SELECT a.building_code, time_between(a.lon,a.lat,b.lon,b.lat) \
                        AS time \
                    FROM gps AS a JOIN (SELECT lon,lat,building_code \
                                        FROM gps WHERE building_code = ?) AS b)\
                    WHERE time <= ?)'
        query_l.append(squery)
    if 'enroll_lower' in args_keys:
        query_l.append('s.enrollment >= ?')
    if 'enroll_upper' in args_keys:
        query_l.append('s.enrollment <= ?')
    if 'terms' in args_keys:
        num_words_2_match = len(args_from_ui['terms'].split())
        squery = ''
        squery += 'c.course_id IN \
            (SELECT x.course_id \
            FROM courses AS c JOIN catalog_index AS x ON (c.course_id = \
                x.course_id) \
            WHERE (c.title LIKE ' + ' OR '.join(['?'] * num_words_2_match) \
                + ') OR (x.word IN (' + ', '.join(['?'] * num_words_2_match) \
                + ')))'
        query_l.append(squery)
    if len(query_l) != 0:
        query += ' AND '.join(query_l)

    return query 

def get_arguments(args_from_ui):
    '''
    Takes a dictionary of criteria for a query and returns its values in an
    ordered list 

    Inputs
        args_from_ui: a dictionary

    Outputs
        arguments_list: a list
    ''' 
    arguments_list = [] 
    order_list = ["dept", "day", "time_start", "time_end", "building", \
    "walking_time", "enroll_lower", "enroll_upper", "terms"]

    for parameter in order_list:
        if parameter in args_from_ui.keys():
            if parameter == "day":
                for day in args_from_ui["day"]:
                    arguments_list.append(day)
            elif parameter == "terms":  
                terms_list = args_from_ui[parameter].split(" ")
                for term in terms_list:
                    arguments_list.append(''.join(['%', term, "%"]))
                for term in terms_list:
                    arguments_list.append(term)
            else:
                arguments_list.append(args_from_ui[parameter])

    return arguments_list

def format_database(query, args, connection):
    '''
    Function that takes a string query, arguments in a list, and a connection
    object. Executes an SQL query using connection.execute() and saves results
    in a list. Returns a tuple with: a list of the headers and a list of the 
    query results.
    
    Inputs
        query: a string
        args: a list
        connection: a connection object

    Outputs
        A tuple with two lists
    '''
    connection.execute(query, args)
    row_list = [] 
    for tuple_value in connection.fetchall():
        row = []
        for item in tuple_value:
            row.append(item)
        row_list.append(row)    

    if len(row_list) == 0:
        return ([],[])
    else:
        return (get_header(connection), row_list)

########### auxiliary functions #################
########### do not change this code #############

def compute_time_between(lon1, lat1, lon2, lat2):
    '''
    Converts the output of the haversine formula to walking time in minutes
    '''
    meters = haversine(lon1, lat1, lon2, lat2)

    #adjusted downwards to account for manhattan distance
    walk_speed_m_per_sec = 1.1 
    mins = meters / (walk_speed_m_per_sec * 60)

    return mins


def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points 
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    m = km * 1000
    return m 

def get_header(cursor):
    '''
    Given a cursor object, returns the appropriate header (column names)
    '''
    desc = cursor.description
    header = ()

    for i in desc:
        header = header + (clean_header(i[0]),)

    return list(header)

def clean_header(s):
    '''
    Removes table name from header
    '''
    for i in range(len(s)):
        if s[i] == ".":
            s = s[i+1:]
            break

    return s

########### some sample inputs #################

example_0 = {"time_start":930,
             "time_end":1500,
             "day":["MWF"]}

example_1 = {"building":"RY",
            "walking_time": 10,
             "dept":"CMSC",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "terms":"computer science"}

example_2 = {"terms":"computer"}

example_3 =  {
             "day":["MWF", "TR","F"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "enroll_upper": 30,
             "terms":"science"}

example_4 = {"dept":"STAT",
             "day":["MWF", "TR","F"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "enroll_upper": 30}
             
example_5 = {"building":"RY",
            "walking_time": 10,
             "dept":"CMSC",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "enroll_upper":30,
             "terms":"computer science"}

example_6 = {"dept":"HIST"}