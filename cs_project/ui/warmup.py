'''
###PART 1: SQL code
sqlite3 ui/course-info.db

# # Question 1
SELECT title
FROM courses
WHERE dept = 'CMSC'

# # Question 2
SELECT c.dept, s.course_id, s.section_num
FROM courses AS c JOIN sections AS s JOIN meeting_patterns AS m ON (c.course_id = s.course_id AND s.meeting_pattern_id = m.meeting_pattern_id)
WHERE m.day = "MWF" AND m.time_start = 1030

# # Question 3
SELECT c.dept, c.course_num
FROM courses AS c JOIN meeting_patterns AS m JOIN sections AS s ON (c.course_id = s.course_id AND m.meeting_pattern_id = s.meeting_pattern_id)
WHERE m.time_start > 1030 AND m.time_end < 1500 AND s.building_code = "RY"

# # Question 4
SELECT c.dept, c.course_num, c.title
FROM courses AS c JOIN meeting_patterns AS m JOIN sections AS s JOIN catalog_index AS x ON (c.course_id = s.course_id AND m.meeting_pattern_id = s.meeting_pattern_id AND s.course_id = x.course_id)
WHERE (m.day = 'MWF') AND (m.time_start = 930) AND (x.word like '%programming%' OR '%abstraction%' OR c.title like '%programming%' OR '%abstraction%')

# Question 4
SELECT dept, course_num, title
FROM courses
WHERE course_id IN (
SELECT s.course_id
FROM sections AS s JOIN meeting_patterns AS m ON (s.meeting_pattern_id = m.meeting_pattern_id)
WHERE m.day = 'MWF' AND m.time_start = 930 AND course_id IN
(SELECT x.course_id 
    FROM courses AS c JOIN catalog_index AS x ON (c.course_id = x.course_id) 
    WHERE (c.title LIKE '%programming%' OR '%abstraction%') OR (x.word LIKE '%programming%' or '%abstraction%'))
);
'''

###PART 2: Python code
import sqlite3
import courses

QUERY_1 = "SELECT title FROM courses WHERE dept = ?"
QUERY_2 = "SELECT c.dept, s.course_id, s.section_num FROM courses AS c JOIN sections AS s JOIN meeting_patterns AS m ON (c.course_id = s.course_id AND s.meeting_pattern_id = m.meeting_pattern_id) WHERE m.day = ? AND m.time_start = ?"
QUERY_3 = "SELECT c.dept, c.course_num FROM courses AS c JOIN meeting_patterns AS m JOIN sections AS s ON (c.course_id = s.course_id AND m.meeting_pattern_id = s.meeting_pattern_id) WHERE m.time_start > ? AND m.time_end < ? AND s.building_code = ?"
QUERY_4 = "SELECT c.dept, c.course_num, c.title FROM courses AS c JOIN meeting_patterns AS m JOIN sections AS s JOIN catalog_index AS x ON (c.course_id = s.course_id AND m.meeting_pattern_id = s.meeting_pattern_id AND s.course_id = x.course_id) WHERE (m.day = ?) AND (m.time_start = ?) AND (x.word like ? OR ? OR c.title like ? OR ?)"
PART_3 = "SELECT building_code, time \
			FROM (SELECT a.building_code, time_between(a.lon,a.lat,b.lon,b.lat) as time\
			FROM gps as a JOIN (SELECT lon,lat,building_code FROM gps WHERE building_code = 'RY') as b)\
			WHERE time <= ?" 

PART_1 = "SELECT lon,lat,building_code FROM gps WHERE building_code = 'RY'"
PART_2 = "SELECT a.building_code, time_between(a.lon,a.lat,b.lon,b.lat) as time\
			FROM gps as a JOIN (SELECT lon,lat,building_code FROM gps WHERE building_code = 'RY') as b\
			WHERE a.building_code != b.building_code AND time <= ?"

connection = sqlite3.connect('ui/course-info.db')
connection.create_function("time_between", 4, courses.compute_time_between)
c = connection.cursor()
c.execute(PART_3,[10])
print(c.fetchall())

x = {"dept":"CMSC","terms":"hector salvador carlos grandet","day":["MWF","TR"],"walking_time":10}


def get_arguments(args_from_ui):
    '''
    Takes a dictionary of criteria for a query and returns
    the values in form of a list 

    args_from_ui: a dictionary
    ''' 
    arguments_list = [] 
    order_list = ["dept", "day","time_start","time_end","building_code",\
                 "enroll_lower","enroll_upper","terms"]

    for parameter in order_list:
        if parameter in args_from_ui.keys():
            if parameter == "day":
                for day in args_from_ui["day"]:
                    arguments_list.append(day)
            elif parameter == "terms":  
                terms_list = args_from_ui[parameter].split(" ")
                for term in terms_list:
                    arguments_list.append(term)
                for term in terms_list:
                    arguments_list.append(term)
            else:
                arguments_list.append(args_from_ui[parameter])

    return arguments_list

# connection = sqlite3.connect('course-info.db')
# connection.create_function("time_between", 4, courses.compute_time_between)

# # For Q1
# args = ['CMSC']
# c = connection.cursor()
# c.execute(QUERY_1, args)
# print(c.fetchall())

# For Q2
# args = ['MWF', 1030]
# c = connection.cursor()
# c.execute(QUERY_2, args)
# print(c.fetchall())

# # For Q3
# args = [1030, 1500, 'RY']
# c = connection.cursor()
# c.execute(QUERY_3, args)
# print(c.fetchall())

# # For Q4
# args = ['MWF', 930, '%programming%', '%abstraction%', '%programming%', '%abstraction%']
# c = connection.cursor()
# c.execute(QUERY_4, args)
# print(c.fetchall())



# args_4 = ['MWF', 930, '%programming%', '%abstraction%', '%programming%', '%abstraction%']
# c = connection.cursor()



def format_database(connection,string,args):
    '''
    Function that takes a string query and arguments in a list and
    returns a lists of lists with the query results
    
    query = a string
    args = a list
    '''
    connection.execute(string,args)
    row_list = [] 
    for tuple_value in connection.fetchall():
        row = []
        for item in tuple_value:
            row.append(item)
        row_list.append(row)    

    database = (courses.get_header(connection), row_list)
    return database
