
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.
import sys
sys.path.insert(0, 'lib')

import json
import urllib2
import httplib
import time
from bs4 import BeautifulSoup
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
	r  = requests.get(url)
	print "URL is "+url
	data = r.text
	print "data: "+data[:100]
	soup = BeautifulSoup(data)
	return soup
def pretty_print(project):
	print json.dumps(data['projects'][0],sort_keys=True,indent=4, separators=(',',': '))

def epoch_to_iso8601(timestamp):
	date = {"__type": "Date","iso": datetime.fromtimestamp(timestamp).isoformat()+".000Z"}
	print date
	return date

def save(project):
	connection.request('POST', '/1/classes/Project', json.dumps(project), {
		"X-Parse-Application-Id": "QlnlX84K0A6TNyjX14aY56EFSMV00eCzdY8SWcuM",
		"X-Parse-REST-API-Key": "VxEy0sA4fkJhBanZXoBkKcoYtZ57AiBvY6gkKfeh",
		"Content-Type": "application/json"
		})
	result = json.loads(connection.getresponse().read())
	return result

def create(project):
	try:
		#dictionary comprehension
		good_keys = ["backers_count","slug","blurb","country","currency","goal","name","pledged"]
		good = { key: project[key] for key in good_keys }

		#flattening out nested dictionaries
		good["category"] = project["category"]["name"]
		good["deadline"] = epoch_to_iso8601(project["deadline"])
		good["creation_date"] = epoch_to_iso8601(project["created_at"])
		good["launch_date"] = epoch_to_iso8601(project["launched_at"])
		good["project_url"] = project["urls"]["web"]["project"]
		good["rewards_url"] = project["urls"]["web"]["rewards"]
		good["proj_id"] = project["id"]
		good["image"] = project["photo"]["1024x768"]
		good["user_id"] = project["creator"]["id"]

		#initialize scraper
		url = good['project_url']
		soup = soupify(url)

		#scrape campaign data
		description = soup.findAll("div", {"class": "full-description"})[0]
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

		return good
	except:
		tb = traceback.format_exc()
		print tb
		#server = setup_server()
		#send(server,tb)
		#server.close()
		return None

page = 1
url = "https://www.kickstarter.com/projects/1567780277/lusids-spaceship-fund?ref=ending_soon"
soup = soupify(url)
a = soup.findAll(attrs={"class":"full-description js-full-description responsive-media formatted-lists"})
