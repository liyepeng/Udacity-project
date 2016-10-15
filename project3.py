# ##Open Street map project
# Packages to be used in the project
import xml.etree.cElementTree as ET 
from collections import defaultdict 
import re 
import pprint 
import codecs 
import json

# Read osm files
OSMFILE = "Houston_texas.osm" 
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
infile = OSMFILE

##pre-compiled regex queries 
#the street type ending, example street, st., road
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
lower = re.compile(r'^([a-z]|_)*$')
#needed to check if lower_colon in name
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$') 
#Problem character searches for the 2 problem values we found in audit 
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Identify number of tags in osm file
def count_tags(filename):
    '''Iterate through each element in the file and add the relevant node name to a dictionary 
     the first time with a value of 1 and then increment by 1 each time that node appears again.''' 
     #initialize defaultdict to avoid KeyError and allow new keys not found in dictionary yet 
      tags = defaultdict(int)
      #iterate through each node element and increment the dictionary value for that node.tag key
      for event, node in ET.iterparse(filename):
            if event == 'end':
                 tags[node.tag]+=1
            # discard the element is needed to clear from memory and speed up processing
            node.clear()              
      return tags 
tags = count_tags('Houston_texas.osm') 
pprint.pprint(tags) 

# Identify Key Type Errors 
# Identify errors function 
# Used by count_key_kinks()
lower = re.compile(r'^([a-z]|_)*$') 
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$') 
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]') 

def key_type(element, keys): 
    if element.tag == "tag": 
        if re.search(lower, element.attrib['k']):         
            keys['lower'] += 1             
        elif re.search(lower_colon, element.attrib['k']): 
            keys['lower_colon'] += 1             
        elif re.search(problemchars, element.attrib['k']): 
            keys['problemchars'] += 1 
            #print out any values with problematic characters 
            #print element             
            print element.attrib['k']             
        else: 
            keys['other'] += 1                       
    return keys 
 
def count_key_kinks(filename): 
    #initialize dictionary 
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0} 
    for _, element in ET.iterparse(filename): 
        keys = key_type(element, keys) 
        # discard the element is needed to clear from memory and speed up processing 
        element.clear() 
    return keys  
 
keys = count_key_kinks('Houston_texas.osm') 
pprint.pprint(keys)

def unique_users(filename): 
    '''Identify unique contributors in osm file'''
    users = set() 
    for _, element in ET.iterparse(filename): 
        try: 
            users.add(element.attrib['uid']) 
        except KeyError: 
            pass 
        element.clear() 
    return users 
users = unique_users('Houston_texas.osm') 
print len(users) 

# List of the street types we expect to see in the US
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",  
            "Trail", "Parkway", "Commons", "Ring Road"]

# Map the 'incorrect' street abbrvs with the correct street names
# Update the mapping by audit street report
Street_mapping = {'AVE': 'Avenue',
 'AVENUE': 'Avenue',
 'Ave': 'Avenue',
 'Ave.': 'Avenue',
 'Blvd': 'Boulevard',
 'Blvd.': 'Boulevard',
 'Broadway': 'Broadway',
 'Bypass': 'Bypass',
 'Circle': 'Circle',
 'Crossing': 'Crossing',
 'Cypress': 'Cypress',
 'DRIVE': 'Drive',
 'Dr': 'Drive',
 'E': 'East',
 'East':'East',
 'Freeway':'Freeway',
 'Frwy':'Freeway',
 'Fwy': 'Freeway',
 'Highway': 'Highway',
 'Ln': 'Lane',
 'Loop': 'Loop',
 'N': 'North',
 'North':'North',
 'Pkwy': 'Parkway',
 'Rd': 'Road',
 'Rd.': 'Road',
 'Riverway': 'Riverway',
 'Road)': 'Road',
 'S': 'South',
 'ST': 'Street',
 'South': 'South',
 'Speedway': 'Speedway',
 'St': 'Street',
 'St.': 'Street',
 'Stree': 'Street',
 'Way': 'Way',
 'West': 'West',
 'blvd': 'Boulevard',
 'street': 'Street',
}

#Mapping postal_code according to the audit postal code report
postal_code_mapping = {'77007-2121': '77007','77005-1890': '77005', '77339-1510': '77339', 
'77027-6850': '77027', '77007-2112': '77007','77007-2113': '77007', 'TX 77009': '77009',
'77025-9998': '77025','77019-1999': '77019', '77042-9998': '77042', 'Weslayan Street': '71000',
'77054-1921': '77054', '77024-8022': '77024', '77478-': '77478', '77036-3590': '77036', '7-': '71000', 
'77077-9998': '77077','TX 77494':'77494','TX 77086':'77086','77584-':'77584','77459-':'77459',
'773867386':'77386', 
}
default_phone_number = "+" + "1 " + "8888888888"

 #Add error street names to street_type
def audit_street_type(street_types, street_name):
    # find street type
    m = street_type_re.search(street_name) 
    if m: 
        street_type = m.group()  #group street_name
        if street_type not in expected:
            street_types[street_type].add(street_name)

# Add error postal codes to postcodes
def audit_postal_code(invalid_postal_codes, postal_code): 
    try: 
        if postal_code[0]== 'u' or postal_code.isdigit() == False or len(postal_code) != 5 : #audit postal code containing strings or length greater than 5 
            raise ValueError 
    except ValueError: 
        invalid_postal_codes[postal_code] += 1 

# Add error phone number or phone number without country code to invalid phone numbers
def audit_phone_number(invalid_phone_numbers, phone_number): 
    try: 
        if phone_number[:2] != '+1':  # targeting phone number without coutry code or start with other wrong strings
            raise ValueError 
        elif len(phone_number) > 17:      # eg +1 (888)-888-888888
            raise ValueError
    except ValueError: 
        invalid_phone_numbers[phone_number] += 1
        
def is_street_name(elem): 
    return (elem.attrib['k'] == "addr:street") 
 
def is_postal_code(elem): 
    return (elem.attrib['k'] == "addr:postcode") 

def is_phone_number(elem): 
    return (elem.attrib['k'] == "phone")

def audit(osmfile): 
    osm_file = open(osmfile, "r") 
    street_types = defaultdict(set) 
    invalid_postal_codes = defaultdict(int) 
    invalid_phone_numbers = defaultdict(int) 
    for event, elem in ET.iterparse(osm_file, events=("start",)): 
        if elem.tag == "node" or elem.tag == "way": 
            for tag in elem.iter("tag"): 
                if is_street_name(tag): 
                    audit_street_type(street_types, tag.attrib['v']) 
                elif is_postal_code(tag): 
                    audit_postal_code(invalid_postal_codes, tag.attrib['v']) 
                elif is_phone_number(tag): 
                    audit_phone_number(invalid_phone_numbers, tag.attrib['v']) 
    return [invalid_postal_codes, invalid_phone_numbers, street_types]

#standardizes street types with a replacement map 
def update_name(name, mapping):
    '''Update each street name with the replacement ending in the mapping dictionary'''
    name = name.split(' ') 
    type = name[-1] 
    if type in mapping: 
        name[-1] = mapping[type] 
        name = ' '.join(name) 
        name = name.title() 
    return name

#checks if postal code within postal code mapping, if it is updating the postal code   
def update_postal_code(postal_code,mapping):
    '''Update each postal code with the replacement ending in the postal code dictionary'''
    try: 
        if len(postal_code) != 5: 
            raise ValueError 
        else: 
            return int(postal_code) 
    except ValueError: 
        type = postal_code
        if type in mapping: 
            postal_code = mapping[type] 
        return postal_code 

#standardizes phone number formatting 
def update_phone_number(phone_number):
    '''Update phone number with '+1 8888888888'  format '''
    phone_number = phone_number.translate(None, ' ()-')
    if len(phone_number) > 10:
        return default_phone_number
    else:
        phone_number = '+1 ' + phone_number
        return phone_number

def shape_element(e):
     """Takes a top level element or tag such as way, node, etc and iterates through each element 
     and 2nd level tag (if applicable). Returns one cleaned 
     node (could be a 'way' as well) which is a dictionary of all the fields later  
     to be converted to a JSON document.     
     """ 
    node = {}  #variable is called node, but it can also be a way
    # 1st level tags
    node['created'] = {} 
    node['pos'] = [0,0] 
    if e.tag == "way": 
        node['node_refs'] = [] 
    if e.tag == "node" or e.tag == "way" : 
        node['type'] = e.tag 
        #attributes 
        for k, v in e.attrib.iteritems(): #iterate through each 1st level attributes of tag 'node' or 'way'
            #latitude 
            if k == 'lat': 
                try: 
                    lat = float(v) 
                    node['pos'][0] = lat 
                except ValueError: 
                    pass 
            #longitude 
            elif k == 'lon': 
                try: 
                    lon = float(v) 
                    node['pos'][1] = lon 
                except ValueError: 
                    pass 
            #creation metadata 
            elif k in CREATED: 
                node['created'][k] = v 
            else: 
                node[k] = v 
        #children 
        for tag in e.iter('tag'): 
            k = tag.attrib['k'] 
            v = tag.attrib['v'] 
            if problemchars.match(k): 
                continue 
            elif lower_colon.match(k): 
                k_split = k.split(':') 
                #address fields 
                if k_split[0] == 'addr': 
                    k_item = k_split[1] 
                    if 'address' not in node: 
                        node['address'] = {} 
                    #streets 
                    if k_item == 'street': 
                        v = update_name(v, Street_mapping)                     
                    #postal codes 
                    if k_item == 'postcode': 
                        v = update_postal_code(v,postal_code_mapping) 
                    node['address'][k_item] = v 
                    continue 
            else:                 
                #phone numbers 
                if(is_phone_number(tag)): 
                    v = update_phone_number(v) 
            node[k] = v 
        #way children 
        if e.tag == "way": 
            for n in e.iter('nd'): 
                ref = n.attrib['ref'] 
                node['node_refs'].append(ref); 
        return node 
    else: 
        return None

def process_map(file_in, pretty = False):
    # Writing Json files
    ''' args is input file and returns a json file '''
    file_out = "{0}.json".format(file_in) 
    data = [] 
    with codecs.open(file_out, "w") as fo: 
        for _, element in ET.iterparse(file_in): 
            el = shape_element(element) 
            if el: 
                data.append(el) 
                if pretty: 
                    fo.write(json.dumps(el, indent=2)+"\n") 
                else: 
                    fo.write(json.dumps(el) + "\n") 
    return data

def audit_report(): 
    audit_data = audit(OSMFILE) 
    # print out auditing street name, telephone number and postal code
    pprint.pprint(audit_data[0]) 
    pprint.pprint(audit_data[1]) 
    pprint.pprint(dict(audit_data[2]))
audit_report() 

#process data and output json file
process_map(OSMFILE, False)

###Importing json file into mongo 
# start a mongod instance using ./mongod 
# open new terminal window and cd to mongo bin folder 
# move records from json to mongo like this.. 
# ./mongoimport --db test --collection Houston111 --file C:\Users\yepeng\Downloads\Houston_texas.osm.json

###  Data overview after cleaning
# Postal_code_sort and city_sort show that this metro extract would perhaps be more aptly named "Metrolina" or the "Houston Metropolitan Area"
#for its inclusion of surrounding cities in the sprawl.So, there will be postal codes unexpected
#in the postal code list of Houston.

from pymongo import MongoClient
client = MongoClient()
db = client.test
postal_code_sort = db.Houston111.aggregate([{"$match":{"address.postcode":{"$exists":1}}},
                                          {"$group":{"_id":"$address.postcode",
                                                     "count":{"$sum":1}}}, 
                                          {"$sort":{"count":-1}}])
#Print out the sorted postal code and check if all the error postal code have been cleaned
for p in postal_code_sort:
    print p
city_sort = db.Houston111.aggregate([{"$match":{"address.city":{"$exists":1}}}, {"$group":{"_id":"$address.city", "count":{"$sum":1}}}, {"$sort":{"count":1}}])
i = 0
for c in city_sort:
    if i < 2:
        print c
        i = i +1
        
#Number of ddocuments,nodes and ways
print "The total number of documents: {0}".format(db.Houston111.find().count())
print "The total number of nodes: {0}".format(db.Houston111.find({"type" : "node"}).count())
print "The total number of ways: {0}".format(db.Houston111.find({"type" : "way"}).count())

#Number of Unique users in Houston, TX
number_of_unique_users = db.Houston111.aggregate([
                                          {"$group" : {
                                             "_id" : "$created.user",
                                             "count" : {"$sum" : 1}
                                                      }
                                          }])
user_count = 0
for doc in number_of_unique_users: user_count += 1
print user_count

#Top 5 contributiry users
top_5_users = db.Houston111.aggregate([
                                      {"$group" : {
                                            "_id" : "$created.user",
                                            "count" : {"$sum" : 1}
                                      }},
                                      {"$sort" : {"count" : -1}},
                                      {"$limit" : 5 }
                                     ])
for doc in top_5_users: print doc

#The five most popular amenities in Houston, TX
five_most_popular_amenities = db.Houston111.aggregate([{"$match" : {"amenity" : {"$exists" : 1}}},
                                                      {"$group" : {"_id" : "$amenity",
                                                                  "count" : {"$sum" : 1}}
                                                      },
                                                      {"$sort" : {"count" : -1}},
                                                      {"$limit" : 5}
                                                     ])
for doc in five_most_popular_amenities: print doc

# Numbers of distinct amenities
distinct_amenities = db.Houston111.distinct("amenity")
number_of_amenities = len(distinct_amenities)
print "The number of distinct amenities: {0}".format(len(distinct_amenities))

# Numbers of schools
number_of_schools = int(db.Houston111.find({"amenity" : "school"}).count())
print "The total number of schools: {0}".format(number_of_schools)

# Numbers of cafes
number_of_cafes = int(db.Houston111.find({"amenity" : "cafe"}).count())
print "The number of cafes: {0}".format(number_of_cafes)

# Number of users appearing only once (having 1 post)                                               
one_post_user = db.Houston111.aggregate([{"$group":{"_id":"$created.user", "count":{"$sum":1}}}, {"$group":{"_id":"$count", "num_users":{"$sum":1}}}, {"$sort":{"_id":1}}, {"$limit":1}])
for user in one_post_user:
    print user

###Additional data exploration using MongoDB queries
#Biggest religion 
biggest_religion = db.Houston111.aggregate([{"$match":{"amenity":{"$exists":1}, "amenity":"place_of_worship"}},
                                                {"$group":{"_id":"$religion", "count":{"$sum":1}}},
                                                {"$sort":{"count":-1}}, {"$limit":1}])
for b in biggest_religion:
    print b

# Most popular cuisines
most_pop_cuisine = db.Houston111.aggregate([{"$match":{"amenity":{"$exists":1}, "amenity":"restaurant"}},
                     {"$group":{"_id":"$cuisine", "count":{"$sum":1}}},
                     {"$sort":{"count":-1}}, {"$limit":2}])
for m in most_pop_cuisine:
    print m  

























