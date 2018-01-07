'''

IMPORTANT:

this program requieres the following modules:

sudo pip install pytz
sudo pip install pyyaml

and can be run using the following line:
python ./postTiming_v3_1.py  -f ./config.yml


RantNRave
Basic script for POST into back4apps,  at required times 
Post values into given class according to the following rules:
 
Social Media System Testing
Data for social media posts is stored in a Back4App parse database. Usually, we create the posts manually, but we want to be able to test having many users so we want an auto testing system.
Each post has some key variables:
-	User 
-	Date/Time
-	Tag (Subject)
-	Category
-	Location (Latitude and Longitude)
-	Others
We want to test different simulated users posting lots of posts to the same three tags.
How the system should work: 



Instead of the system triggering every four hours, 
we instead want it to only function from 10 AM - 2 PM PST, every day. 
Instead of the random arrays of posts, we would prefer to instead 
post all the posts for an hour at the same time, at the start
of the hour - the system should be asleep otherwise. 
Additionally, the system should also get the number of posts 
from a .yml file, instead of being randomly generated.


By now, you understand that we have various columns in the "Posts" class. 
What goes into some of these columns is simple, and what fills other columns 
is described in the pseudo code. 

The User column is a pointer to the user class in Back4App

While senderId and userId are the same, the Author column comes from the "username" column in the users class
1) [5QdECR7A1U, 1Tl4u2SJ7C, rjVpsJSrhU] - these are the Ids you should be using. 
These IDs also correspond to the SenderId  columns.
2) While senderId and userId are the same, the Author column comes from the "username" column in the users class
For the objectId class, this is generated uniquely every time a new post is made. 
3) The hashtag class can always be #test. 
4) upVotes and downVotes will always be 0. 
5) There is no need to fill the EventLocationTitle class. 
6) ACL will always be "Public Read and Write."
7) Anonymous will always be false.  
8) RantOrRave will always be Rave 
9) Category will always be "Food"
10) For @tag and the currentLocation columns, here are your pairs. 
  @starbucks - 47.612686, -122.344920
  @tacotruck - 47.612089, -122.344008 
  @grillking - 47.610369, -122.341335
'''	

from 		datetime 		import 	datetime
import 										os
import 										getopt
import 										sys
import 										re
import 										time
import 										random
import 										json
import 										httplib
import 										pytz
import 										yaml
import 										os.path

# tags to be posted. 
# in case of 'extra' post,  two aditional values are required:  addAmount (10 as stated before) and addAtHour:  0: first hour, 1: second hour, and so on
configTagList = [{"Tag": "@starbucks", "Latitude": 47.612686, "Longitude": -122.344920, "lowerTimes": 25, "upperTimes": 35 }, 
		{"Tag": "@tacotruck", "Latitude": 47.612089, "Longitude": -122.344008 , "lowerTimes": 5, "upperTimes": 10},
		{"Tag": "@grillking", "Latitude": 47.610369, "Longitude": -122.341335, "lowerTimes": 5, "upperTimes": 20, "addAtHour": 2, "addAmount": 10}]

sleepInterval = 30	# default

#------------------------------------------------------------------------------------------------

# basic class for handling POST timing
class timeControl(object):
	tag = None

	currentHour = -1			# to detect hours change
	previousHour = None
	
	hour = None
	tag = None
	postQtty = None
	
	# ---------------------   
	def __init__(self, tag, hour, lowerLimit, upperLimit):
		self.tag = tag
		self.hour = hour
		
		self.postQtty = random.randint( lowerLimit, upperLimit )
		print "Post for tag: " + tag + " at hour: " + str(self.hour) + " --> " + str(self.postQtty )
		
	# ---------------------   
	# simple getter
	def getTag(self):
		return self.tag
		
	# ---------------------   
	# simple getter
	def getHour(self):
		return self.hour

	# ---------------------   
	# simple getter
	def getPostQtty(self):
		return self.postQtty

#------------------------------------------------------------------------------------------------

class rantrave(object):

	userList = None
	tagList = None
	hourChanged = False
	hour=None
	hourNumber=None
		
	
    # ---------------------   
	def __init__(self):
		
		self.userList = ["5QdECR7A1U", "1Tl4u2SJ7C","rjVpsJSrhU"]		# list of possible Senders
		 
		self.tagList = [{"Tag": "@starbucks", "Latitude": 47.612686, "Longitude": -122.344920}, 
		{"Tag": "@tacotruck", "Latitude": 47.612089, "Longitude": -122.344008},
		{"Tag": "@grillking", "Latitude": 47.610369, "Longitude": -122.341335}]

    # ---------------------   		
	# build 'random' json-formated-chunk for class 'POST'  and return as string
	# in this case TAG and coordinates are received as parameters
	def buildRandomPostStringForTag(self, tag, latitude, longitude):
		downVotes = upVotes = 0		# fixed so far...
		senderId = UserID = self.userList[random.randint(0,len(self.userList)-1)]   # random, from list
		
		author = self.getUsernameForUserID(UserID)
		postStr = {"Hashtags": "#test",
			"downVotes": downVotes,
			"User": {"__type":"Pointer","className":"_User","objectId":UserID},
			"ACL": {"*": {"read": "true", "write": "true"}},
			"currentLocation": {"__type": "GeoPoint", "latitude": latitude, "longitude": longitude},
			"atTagArray": [tag],
			"AtTags": tag,
			"Anonymous": False,
			"hashTagArray": ["#test"], 
			"upVotes": upVotes,
			"senderId": senderId,
			"RantOrRave": "Rave",
			"Category": "Food",
			"author": author,
			"Comment": "rfurch"}		
		return postStr		

    # ---------------------
    # get Username from table USER in Back4app, corresponding to a given USER ID 
	def getUsernameForUserID(self, userID):
		
		username = 'Unknown'	
		app_id = "SZHjevT3j3m0UHan9OurbdjNFrVlSkWuARZUFieI"
		rest_key = "BdJsu7iVYyOEykyiLBvM7nOjoBODrqvxCDprftMY"
		headers = {
			'Content-type': 'application/json',
			'X-Parse-Application-Id': app_id,
			'X-Parse-REST-API-Key': rest_key
			}
	
		connection = httplib.HTTPSConnection('parseapi.back4app.com', 443)
		connection.connect()
		connection.request('GET', '/classes/_User/' + str(userID), '', headers)
		results = json.loads(connection.getresponse().read())
		#print results

		if len(results):
			username = results.get('username')
		return username
		
    # ---------------------
    # send data via RESTAPI to Back4app and dump result to log file    
	def postDataToPostClass(self, postStr):
			
		jsonStr = json.dumps(postStr) 
		print (jsonStr)
		app_id = "SZHjevT3j3m0UHan9OurbdjNFrVlSkWuARZUFieI"
		rest_key = "BdJsu7iVYyOEykyiLBvM7nOjoBODrqvxCDprftMY"
		headers = {
			'Content-type': 'application/json',
			'X-Parse-Application-Id': app_id,
			'X-Parse-REST-API-Key': rest_key
			}
	
		connection = httplib.HTTPSConnection('parseapi.back4app.com', 443)
		connection.connect()
		connection.request('POST', '/classes/Post', jsonStr, headers)
		results = json.loads(connection.getresponse().read())
		print results
 
#--------------------------------------------------------------------------------

def usage():
	print ("\n\n")
	print ("Back4APPS POST robot:")
	print ("-c class (eg: Post, User, etc.).  REQUIRED")
	print ("-f config filename. REQUIRED")
	print ("-v [Optional verbosity level.  the more 'v' the more verbose!]")
	print ("-h [Print this message]")	 
	print ("\n\n")

#--------------------------------------------------------------------------------
#  simple funcition to trigger random tag Post  according with definitions 

def timeLoop(timeControlList):
	
	tagList = []	
	previousHour=-1	
	currentHour = -1
	
	while True:
		tz = pytz.timezone('US/Pacific')	
		pst_time = datetime.now(tz)
		print pst_time
		currentHour = pst_time.hour
		print currentHour
	
		# we only check on every hour change.   
		# pay attention to the fact that if program is started within a valid hour
		# all POSTS will take place immediately !
		
		if currentHour != previousHour:
			for n in timeControlList:
				if n.getHour() == currentHour:
					tag = n.getTag()
					postQtty = n.getPostQtty()
					lat = [y for y in configTagList if y['Tag']==tag][0].get('Latitude')
					lon = [y for y in configTagList if y['Tag']==tag][0].get('Longitude')

					print "\n ---- Generating: " + str(postQtty) + " Posts for tag: "   + str(tag) + "-----\n"
					for i in range(postQtty):
						rr = rantrave()
						strData = rr.buildRandomPostStringForTag(tag, lat, lon)
						print str(strData) + "\n"	
						# uncomment for posting
						rr.postDataToPostClass(strData)

			previousHour = currentHour

		time.sleep(sleepInterval)
		
#--------------------------------------------------------------------------------
# read config file with the following format:
'''
sleep_interval: 30
1100:
  '@tacotruck':
  - min:5
  - max:20
  '@grillking':
    - min:5
    - max:10
  '@starbucks':
      - min:35
      - max:40
'''

def readConfigFile(fileName):
	
	tcontrol = []
	
	if os.path.isfile(fileName):
		with open(fileName, 'r') as ymlfile:
			cfg = yaml.safe_load(ymlfile)

		# loaddata from YAML file, with default values in case of error

		for key in cfg:
			if str(key).lower() == 'sleep_interval':
				sleepInterval = int(cfg[key])
				print "Sleep Interval: " + str(sleepInterval) + " seconds."
			else:
				randomMin = 0
				randomMax = 0
				hour = int(key) / 100	
				for value in cfg[key]:
					tag = value
					randomRange =  cfg[key][value]
					
					for aux in randomRange:
						val = aux.split(":")
						if val[0].lower() == 'min':
							randomMin = int (val[1])
						elif val[0].lower() == 'max':
							randomMax = int (val[1])

					if len(tag) > 1:
						print "Add new timedPost for hour: " + str(hour) + " tag: " + str (tag) + " randomMin: " + str(randomMin) + " randomMax: " + str(randomMax)
						tcontrol.append(timeControl(tag, hour, randomMin, randomMax))
	else:
		print "File: " + fileName + " not found!!!"
		sys.exit (0)
		
	return tcontrol
	
#--------------------------------------------------------------------------------

def main():
	className=None
	seconds=None
	configFilename="./config.yml"
	timeControlList = []

	try:
		opts, args = getopt.getopt(sys.argv[1:], "f:c:vh", ["help", "verbose"])
	except getopt.GetoptError as err:
		# print help information and exit:
		print (str(err))  # will print something like "option -a not recognized"
		usage()
		sys.exit(2)

	for o, a in opts:
		if o in ("-v", "--verbose"):
			_verbose+=1
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-f"):
			configFilename = a
		elif o in ("-c"):
			className = a
						
		else:
			assert False, "unhandled option"

	random.seed(time.time())		# initialize random seed with seconds at start
	timeControlList = readConfigFile(configFilename)  # load config from file into list of objects
	timeLoop(timeControlList)		## timing loop for control and posting  
	
#--------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
    
#--------------------------------------------------------------------------------



