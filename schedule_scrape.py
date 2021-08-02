from bs4 import BeautifulSoup
from pymongo import MongoClient
from progress.bar import ShadyBar
import requests, pandas, csv, re
from secret import user, passwd, url

TERMS_TO_UPDATE = 99 # The X most recent terms

def regtime(time):
	reged = []
	segments = re.findall('(\d{1,2})|([AP]M)', time)
	# Hour is only converted if in PM and not in the 13th hour (12-12:59 don't get bumped)
	if(segments[2][1] == 'PM' and segments[0][0] != '12'):
		reged.append(str(int(segments[0][0]) + 12))
	else:
		reged.append(segments[0][0])
	#
	reged.append(segments[1][0])
	if(len(reged[0]) < 2):
		reged[0] = '0' + reged[0]
	return ':'.join(reged)
#

def standardize(days_times, room, dates):
	days_times = days_times.upper()
	if(days_times == '' or 'TBA' in days_times or 'TBA' in room or 'TBA' in dates):
		return
	day_map = { 'MO': 'Mo', 'TU': 'Tu', 'WE': 'We', 'TH': 'Th', 'FR': 'Fr', 'SA': 'Sa', 'SU': 'Su'}
	obj = {}
	# obj.days, obj.start, obj.finish, obj.begin, obj.complete, obj.room
	# ((Mo)|(Tu)|(We)|(Th)|(Fr))+
	days = ''
	if days_times[0] == '-':
		days = 'SU'
	else:
		days = re.match('((MO)|(TU)|(WE)|(TH)|(FR)|(SA)|(SU))+', days_times).group(0)
	times = re.findall('(\d{1,2}:\d{1,2}((AM)|(PM)))', days_times)

	if len(times) == 0: # Catch courses with no defined class time (Web based courses, Desktop-Async, etc)
		times = [('12:00AM', 'AM', 'AM', ''), ('12:01AM', 'AM', 'AM', '')]

	times = [regtime(times[0][0]), regtime(times[1][0])]

	i = 0
	cleanDays = ''
	while i < len(days):
		cleanDays += day_map[days[i] + days[i + 1]]
		i += 2

	obj['days'] = cleanDays
	obj['room'] = room
	obj['start'] = times[0]
	obj['finish'] = times[1]
	if(dates != ''):
		if '-' not in dates: # Catch courses that are only 1 day (no end date)
			dates = dates + ' - ' + dates
		dates = re.findall('(\d{1,2}\/\d{1,2}\/\d{4})', dates)
		obj['begin'] = dates[0]
		obj['complete'] = dates[1]
	else:
		obj['begin'] = ''
		obj['complete'] = ''
	return obj
#

def course_to_obj(course):
	obj = {}
	obj['sis_id'] = course[0]
	obj['subject'] = course[1]
	obj['catalog_number'] = course[2]
	obj['common_name'] = course[1] + course[2]
	obj['section'] = course[3]
	obj['type'] = course[4]
	obj['credits'] = course[5]
	obj['title'] = course[22]
	obj['topic'] = course[23]
	obj['status'] = course[24]
	obj['enrolled'] = course[25]
	obj['enroll_limit'] = course[26]
	obj['waiting'] = course[27]
	obj['desc'] = course[28]
	obj['instructors'] = []
	for i in [6, 10, 14, 18]:
		if(course[i] != ''):
			obj['instructors'].append(course[i])
	assign = []
	for i in range(0, 4):
		x = standardize(course[7 + (i * 4)], course[8 + (i * 4)], course[9 + (i * 4)])
		if x:
			assign.append(x)
	#
	obj['meetings'] = assign
	return obj
#

# Old url: http://rabi.phys.virginia.edu/mySIS/CS2/index.php
def getTerms():
	print('Scraping terms list\n')
	searchPage = BeautifulSoup(requests.get('https://louslist.org/').text, features='html.parser')
	semesters = searchPage.find('select').find_all('option')
	terms = []
	with ShadyBar('', max=len(semesters), suffix='%(percent).1f%% - %(eta)d s  ') as bar:
		for opt in semesters:
			friendly = opt.text[:-9] # Friendly name is Fall 2019, Spring 2019, January 2019, Summer 2019
			abbrev = friendly[:2] if 'Summer' in friendly else friendly[0]
			short = abbrev + friendly[-2:] # Short name consists of something like this: F18, S18, Su18, J18
			terms.append({'_id': opt.get('value')[-4:], 'name': opt.text, 'friendly': friendly, 'short': short})
			bar.next()
	#
	return terms
#

# Old urll: http://rabi.phys.virginia.edu/mySIS/CS2/deliverData.php
def parseTerm(term):
	print('\n--------------------\nProcessing\n', term['name'], '...')
	fall_data_raw = requests.post('https://louslist.org/deliverData.php', data = {'Group': 'CS', 'Semester': term['_id'], 'Description': 'Yes', 'Extended': 'Yes'})
	fall_data = list(csv.reader(fall_data_raw.text.splitlines(), delimiter=','))
	coll = db['term_' + term['_id']]
	max = len(fall_data)
	with ShadyBar('', max=max-1, suffix='%(percent).1f%% - %(eta)d s  ') as bar:
		for i in range(1, max):
			obj = course_to_obj(fall_data[i])
			coll.find_one_and_update({"sis_id": obj['sis_id']}, {'$set': obj}, upsert=True)
			bar.next()
		#
	#
#


# Now that we have all available terms at the ready, we know the following:
# 	a) the most recent term is the first index of that list.
# 	b)
# ^^ it has been 2 years since I wrote this comment, and I never wrote anything for (b), but
#    now there is no hope of knowing what I had planned to write there!

try:
	client = MongoClient(f'mongodb+srv://{user}:{passwd}@{url}/test?retryWrites=true&w=majority')
	db = client.course_data
	available_terms = getTerms()
	print('\n--------------------\nUpdating terms list...\n')
	with ShadyBar('', max=len(available_terms)-1, suffix='%(percent).1f%% - %(eta)d s  ') as bar:
		for term in available_terms:
			coll = db['terms']
			coll.find_one_and_replace({'_id': term['_id']}, term, upsert=True)
			bar.next()
		#
	#
	available_terms = available_terms[:TERMS_TO_UPDATE]
	max = len(available_terms)
	for i in range(0, max):
		parseTerm(available_terms[i])
	#
except KeyboardInterrupt:
	print('Process terminated early.')
#
