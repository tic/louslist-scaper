# Mongo course loader
# Loads / updates courses in MongoDB

# !!! Requires dnspython, pymongo, termer.py to run

from pymongo import MongoClient
import requests, json
import termer

# Keys to map the raw course data into a more
# Mongo / user friendly format.
json_keys = ['subject', 'catalog_number', 'section', 'sis_id', 'title', 'desc', 'instructor', 'enrollment_max', 'days', 'meeting_start', 'meeting_end', 'term_id', 'term_name']

# Generate the Mongo connection URI.
from secret import user, passwd, url
uri = f'mongodb+srv://{user}:{passwd}@{url}/test?retryWrites=true&w=majority'


###########################################
########### Main Update Routine ###########
###########################################
def update_dbs(term_data):
	# Get list of collections in Mongo
	client = MongoClient(uri)
	db = client.course_data
	collections = db.list_collection_names()
	
	def term_exists(col):
		for i in range(0, len(collections)):
			if col in collections[i]:
				return i
		return -1
	#
	
	def course_to_json(course):
		entry = {}
		for index in range(0, len(json_keys)):
			entry[json_keys[index]] = course[index]
		#
		return entry
	#
	
	coll = db['terms']
	for term in term_data[1]:
		matches = coll.find({'term_id': term[0]})
		try:
			matches.next()
			coll.replace_one({'term_id': term[0]}, {'term_id': term[0], 'name': term[1]})
			print('Updated existing term', term[0])
		except StopIteration:
			coll.insert_one({'term_id': term[0], 'name': term[1]})		
			print('Created new record for term', term[0])
		#
	#
	
	for item in term_data[0]:
		# item['term'] -> this term id
		# item['courses'] -> courses for this term
		collection_index = term_exists(item['term'])
		if collection_index > -1:
			collection = db[collections[collection_index]]
			i = 1
			l = len(item['courses'])
			for course in item['courses']:
				course = course_to_json(course)
				collection.find_one_and_replace({'sis_id': course['sis_id']}, course, upsert=True)
				print('Updated', course['term_name'], '(' + str(i) + '/' + str(l) + ')', ':', course['sis_id'], '-- ', course['subject'], course['catalog_number'])
				i = i + 1
			#
		else:
			# Create a new collection for this term,
			# then put all it's classes inside.
			new_collection = db['term_' + item['term']]
			print('Created collection', 'term_' + item['term'])
			for course in item['courses']:
				new_collection.insert_one(course_to_json(course))
			#
		#
	#
	client.close()
#

###########################################
########### Execute the update ############
###########################################
try:
	all_term_data = termer.get_all_terms();
	update_dbs(all_term_data)
	print('Done!')
except KeyboardInterrupt:
	print('User terminated process early')
