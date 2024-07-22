# AU Job Scraping Tool

This Python script scrapes job listings from Seek.com.au for various job titles and stores the results in a MySQL database. It also saves the data as CSV files.

## Prerequisites

- Python 3.x
- `requests` library
- `beautifulsoup4` library
- `pandas` library
- `pymysql` library

You can install the required libraries using pip:

```sh
pip install -r requirements.txt
```
Database Configuration
Update the DB_CONFIG dictionary in the script with your MySQL database details:
```
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'your_database_name',
    'user': 'your_database_user',
    'password': 'your_database_password',
    'cursorclass': DictCursor
}
```
Job Titles and Location
You can customize the job titles and location by modifying the JOB_TITLES and LOCATION variables:

python
Copy code
JOB_TITLES = ["Data Analyst", "Credit Analyst", "Credit Risk Analyst", "Compliance Analyst", "Market Risk Analyst", "Software Developer"]
LOCATION = "Sydney NSW 2000"
Other Configurations
SALARY_RANGE: Specify the salary range if needed.
SALARY_TYPE: Specify the salary type if needed.
PAGES_TO_SEARCH: Number of pages to scrape for each job title.
SLEEP_TIME: Time to wait between requests to avoid overloading the server.
Running the Script
Run the script using the following command:

sh
Copy code
python seekscraping.py
The script will scrape job listings for the specified job titles and location, and save the data to the MySQL database and as CSV files.
