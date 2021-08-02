# This is used as a library file by mongo_course_loader.py
# so make sure you have it in the same directory.

import requests, json

# Retrieve the full course list from the Devhub API.
def get():
	print('Fetching API data')
	return requests.get('https://api.devhub.virginia.edu/v1/courses').json()
#

# Look through the full course list and find which
# terms (semesters) are available in it.
def get_terms(data):
	terms = []
	print('Gathering available terms')
	for course in data['class_schedules']['records']:
		if [course[11], course[12]] not in terms:
			terms.append([course[11], course[12]])
		#
	#
	print('Term list acquired')
	return terms
#

# Isolate and return all classes in the data set
# belonging to the specified term.
def find_term(term, data):
	courses = data['class_schedules']['records']
	matches = []
	for course in courses:
		if term == course[11]:
			matches.append(course)
		#
	#
	return matches
#

# Write a given term's course schedule to file.
# Output files are formatted term_<term_id>.json
def write_term(term, data):
	term_data = find_term(term[0], data)
	json_out = {}
	json_out['courses'] = term_data
	print('Writing term', term[0], 'to file')
	with open('term_' + term[0] + '.json', 'w') as f:
		json.dump(json_out, f)
		f.close()
	#
	print('Wrote term', term[0], 'to file')
#

# Write all terms from the data set to their
# respective .json files.
def write_all_terms():
	all_data = get()
	terms = get_terms(all_data)
	print('Writing all terms to file...')
	for term in terms:
		write_term(term, all_data)
	#
#

# Creates an array of json objects where each json
# has a term id and an array of classes from the
# corresponding term.
def get_all_terms():
	all_data = get()
	terms = get_terms(all_data)
	all_terms_data = []
	for term in terms:
		all_terms_data.append({
			'term': term[0],
			'courses': find_term(term[0], all_data)
		})
	#
	print('Returning all terms data')
	return [all_terms_data, terms]
#

#write_all_terms()