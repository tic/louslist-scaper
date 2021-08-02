import requests, re
from pymongo import MongoClient
from bs4 import BeautifulSoup
from secret import user, passwd, url

client = MongoClient(f'mongodb+srv://{user}:{passwd}@{url}/test?retryWrites=true&w=majority')

base_url = 'http://records.ureg.virginia.edu/'
initial_url = 'http://records.ureg.virginia.edu/index.php'

page = requests.get(initial_url)
soup = BeautifulSoup(page.text, 'html.parser')

sidebar = soup.find_all(class_='n2_links')

program_type = [
	'major',
	'minor',
	'concentration',
	'certificate',
	'academic',
	'major',
	'academic'
]

school_map = {
	'School of Engineering and Applied Science': 'SEAS',
	'College of Arts & Sciences': 'CLAS',
	'College of Arts and Sciences': 'CLAS',
	'School of Architecture': 'ARCH',
	'School of Continuing and Professional Studies': 'SCPS',
	'McIntire School of Commerce': 'COMM',
	'Curry School of Education and Human Development': 'CURRY',
	'School of Education and Human Development': 'CURRY',
	'Frank Batten School of Leadership and Public Policy': 'BATTEN',
	'School of Nursing': 'NURS',
	'ROTC': 'ROTC',
	'Return to School of Data Science': 'DS',
	'School of Data Science': 'DS',
}

def createObj(program, school, x, description, link):
	document = {
		'name': program,
		'school': school,
		'type': program_type[x],
		'desc': description,
		'link': link,
	}
	return document
#

def cleanStr(dirty):
	x = re.sub('( Departments/Programs| Programs/Courses)$', '', re.sub(': [^:]*$', '', dirty))
	if('scps' in x):
		return 'SCPS'
	if(len(x) > 55): # Batten has the longest name
		return 'SCPS*'
	return school_map[x]
	#        ^.*: .*$
#

def toMongo(document):
	print('Uploading', document['name'], 'from', document['school'])
	col = client.course_data.programs
	col.replace_one({'name': document['name']}, document, True)
	#
#

def ulsToItems(ul_list):
	x = 0
	for ul in ul_list:
		print('\n=====\nStaring Iteration\n=====\n')
		for li in ul.find_all('li'):
			link = li.find('a')
			# Get name: link.text
			# Get url to preview: link.get('href')
			preview_url = base_url + link.get('href')
			preview_soup = BeautifulSoup(requests.get(preview_url).text, 'html.parser')
			
			school = 'N/A'
			desc = 'Not Provided'
			try:
				ps = preview_soup.find('td', {'colspan': '4'}).find_all('p')
				p = ps[1]
				if(p.find('a') is None):
					# No a, so get span; aside from the APMA exception
					if(link.text == 'Applied Mathematics Program' or 'Engineering' in link.text):
						school = 'SEAS'
					elif('McIntire' in link.text):
						school = 'COMM'
					else:
						school = cleanStr(p.find('span').text)
				else:
					school = cleanStr(p.find('a').text)
				if(len(ps[2].text) > 25):
					desc = ps[2].text
			except IndexError:
				pass
			#
			toMongo(createObj(link.text, school, x, desc, base_url + link.get('href')))
		#
		x = x + 1
	#
#

for item in sidebar:
	link = item.find('a')
	if link.contents[0] == 'Programs':
		programs_url = base_url + link.get('href')
		print('Scraping program data from', programs_url)
		programs_soup = BeautifulSoup(requests.get(programs_url).text, 'html.parser')
		table_uls = programs_soup.find_all('ul', class_='program-list')
		try:
			ulsToItems(table_uls)
		except KeyboardInterrupt:
			print('User interrupted operation')
	#
#

print('\nDone!')
client.close()






