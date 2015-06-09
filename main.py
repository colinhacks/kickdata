from flask import Flask
app = Flask(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.
import sys
sys.path.insert(0, 'lib')

import json
import urllib, urllib2

import httplib
import time
from BeautifulSoup import BeautifulSoup
import requests
from datetime import datetime
from email.mime.text import MIMEText as MIME
import traceback
import smtplib

# Credentials (if needed)
username = 'colinmcd94'  
password = 'mensetmanus' 

"""
def setup_server():
	# The actual mail send  
	server = smtplib.SMTP('smtp.gmail.com:587')  
	server.starttls()  
	server.login(username,password)
	return server

def send(server,msg):
	m = MIME(msg)
	m['Subject'] = "Error in kickdata script"
	m['From'] = 'Colin McDonnell <colinmcd94@gmail.com>'
	m['To'] = "colinmcd@mit.edu"
	server.sendmail(m["From"], m["To"].split(","), m.as_string())
	
"""

def minutes_left(proj):
	deadline = proj["deadline"]
	current = time.time()
	minutes_left = (deadline-current)/60
	return minutes_left

def soupify(url):
	print "SOUPIFYING"
	data  = urllib2.urlopen(url)
	print "URL is "+url
	#data = r.text
	#print "data: "+data[:100]
	soup = BeautifulSoup(data)
	return soup

def pretty_print(project):
	print json.dumps(data['projects'][0],sort_keys=True,indent=4, separators=(',',': '))

def epoch_to_iso8601(timestamp):
	date = {"__type": "Date","iso": datetime.fromtimestamp(timestamp).isoformat()+".000Z"}
	print date
	return date

def save(cxn,project):
	cxn.request('POST', '/1/classes/Project', json.dumps(project), {
		"X-Parse-Application-Id": "QlnlX84K0A6TNyjX14aY56EFSMV00eCzdY8SWcuM",
		"X-Parse-REST-API-Key": "VxEy0sA4fkJhBanZXoBkKcoYtZ57AiBvY6gkKfeh",
		"Content-Type": "application/json"
		})
	result = json.loads(cxn.getresponse().read())
	return result

def create(project):
	try:
		#dictionary comprehension
		good_keys = ["backers_count","slug","blurb","country","currency","goal","name","pledged"]
		good = { key: project[key] for key in good_keys }

		#flattening out nested dictionaries
		good["category"] = project["category"]["name"]
		good["project_deadline"] = epoch_to_iso8601(project["deadline"])
		good["creation_date"] = epoch_to_iso8601(project["created_at"])
		good["launch_date"] = epoch_to_iso8601(project["launched_at"])
		good["project_url"] = project["urls"]["web"]["project"]
		good["rewards_url"] = project["urls"]["web"]["rewards"]
		good["proj_id"] = project["id"]
		good["image"] = project["photo"]["1024x768"]
		good["user_id"] = project["creator"]["id"]

		#initialize scraper
		url = good['project_url']
		print "#################\nURL: "+url+"\n#######################"
		soup = soupify(url)

		#scrape campaign data
		description_div = soup.findAll(attrs={"class":"full-description js-full-description responsive-media formatted-lists"})
		print "Desc_div: "+str(len(description_div))
		if description_div:
			description = description_div[0]
			good["campaign_text"] = description.text

			video_player = soup.findAll("div", {"class": "video-player"})
			if video_player:
				video = video_player[0]
				good["campaign_video"] = video["data-video-url"]

			desc_imgs = description.findAll("img")
			if desc_imgs:
				good["campaign_images"] = [div["src"] for div in desc_imgs]

			desc_iframes = description.findAll("iframe")
			if desc_iframes:
				good["campaign_secondary_videos"] = [div["src"] for div in desc_iframes]
		else:
			print "No description found."
		return good
	except:
		tb = traceback.format_exc()
		print tb
		#server = setup_server()
		#send(server,tb)
		#server.close()
		return None



@app.route('/')
def hello():
	"""Return a friendly HTTP greeting."""
	return 'Hello World!'

@app.route('/scrape')
def scrape():

	page = 1
	more = True
	while more:
		data = json.load(urllib2.urlopen('https://www.kickstarter.com/discover/advanced.json?google_chrome_workaround&page='+str(page)+'&category_id=0&woe_id=0&sort=end_date'))
		projects = data["projects"]
		connection = httplib.HTTPSConnection('api.parse.com', 443)
		connection.connect()
		for project in projects:
			if minutes_left(project)<10:
				final = create(project)
				if final:
					print final["name"]

					#check for duplicate
					params = urllib.urlencode({"where":json.dumps({
				       "proj_id": final["proj_id"]
				     }),"count":1,"limit":0})

					connection.request('GET', '/1/classes/Project?%s' % params, '', {
					       "X-Parse-Application-Id": "QlnlX84K0A6TNyjX14aY56EFSMV00eCzdY8SWcuM",
					       "X-Parse-REST-API-Key": "VxEy0sA4fkJhBanZXoBkKcoYtZ57AiBvY6gkKfeh"
					     })
					result = json.loads(connection.getresponse().read())
					print "Duplicates checK:"
					print result
					duplicates = result["count"]
					if duplicates == 0:
						print "No duplicates, saving object."
						resp = save(connection,final)
						print resp
					else:
						print "Duplicate found.  Not saving object."

			else:
				print "Not enough time.  Breaking out of loop."
				more = False
				break
		connection.close()
		print "Cxn closed."
		page = page + 1
	print "SCRAPE SUCCESSFUL."
	return "Scrape successful."


@app.errorhandler(404)
def page_not_found(e):
	"""Return a custom 404 error."""
	return 'Sorry, nothing at this URL.', 404

