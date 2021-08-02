### Features

- Fetch course data from the <abbr title="University of Virginia">UVA</abbr> DevHub courses API (legacy format)
- Scrape program data from the UVA Registrar (majors, minors, certificates, etc.)
- Download data from [Lous List](https://louslist.org/)
- MongoDB Atlas Integration for uploading and updating course data
- Standardize all course information into a single, easy to use format
- Prepare data for use by the [Scheduler](https://github.com/UVA-Development-Hub/Scheduler) backend API

# UVA Course Scrapers

Below, I briefly explain each file to outline its purpose, how it can be used, and what I used it for when I wrote it.

#### A brief note regarding MongoDB integration
---
The main scripts (mongo_course_loader.py, program_scraper.py, and schedule_scrape.py) all have existing methods for interfacing with MongoDB. Therefore, installing the MongoClient python package is required for every script. If you don't need a MongoDB integration, you will need to comment out the following lines in each script:

|             File               |          Lines to comment         |
| ---------------------- | ----------------- |
| `program_scraper.py` | 2, 4, 6, 65-66, 122 |
| `schedule_scrape.py`  | 2, 5, 118, 122-123, 137, 143-144 |

Notice that `mongo_course_loader.py` is not in this table. This is because the core functionality is so integrated with MongoDB that without it, the script has no real purpose.

## program_scraper.py
** About:** This script is used to scrape data about programs at UVA from the website of the [University Registrar](https://registrar.virginia.edu). This includes data about the majors, minors, certificates, and other academic programs available at the University, including what schools they are taught in (College of Arts &amp; Sciences, School of Engineering and Applied Science, etc.).

**Instructions for Running:** First, you will need to install these packages:
- requests
- re
- MongoClient
- BeautifulSoup

After installing the required packages, start the script with a simple command:
> `$ python program_scraper.py`

**Design Purpose:** Originally, this script was created to supply the Scheduler API with data regarding the different majors and minors offered at the University. This allows a scheduling site to give users options for setting their major/minor and, eventually, showing what the requirements are for the programs they have selected.


## schedule_scrape.py
**About:** Fetches data from Lous List on a semesterly basis, parses it, and reformats into something more suitable for an API to query against.

**Instructions for Running:** First, you will need to install these packages:
- requests
- re
- MongoClient
- BeautifulSoup
- ShadyBar
- pandas
- csv

After installing the required packagfes, start the script with a simple command:
> `$ python schedule_scrape.py`

**Design Purpose:** Originally, this script supplied the Scheduler API with data for all courses offered at the University from all semesters since the fall of 2008. More generally, though, it takes data from Lous List and standardizes it across all semesters and displays it in a consistent and easy to use format.

