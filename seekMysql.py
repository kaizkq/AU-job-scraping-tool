import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import datetime
import pymysql
from pymysql.cursors import DictCursor

# List of job titles
JOB_TITLES = ["Data Analyst",
              "Credit Analyst",
              "Credit Risk Analyst",
              "Compliance Analyst",
              "Market Risk Analyst",
              "Software Developer"]

LOCATION = "Sydney NSW 2000"
SALARY_RANGE = ""
SALARY_TYPE = ""
PAGES_TO_SEARCH = 20
SLEEP_TIME = 2

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': '',
    'user': '',
    'password': '',
    'cursorclass': DictCursor
}

# DB_CONFIG = {
#     'host': 'localhost',
#     'port': 3306,
#     'database': 'job_data_test',
#     'user': 'root',
#     'password': '123456',
#     'cursorclass': DictCursor
# }

def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_job_listings(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    job_listings = []

    articles = soup.find_all('article', class_='_1047lqyb')

    for article in articles:
        job = {}

        # Extract job title
        title_elem = article.find('a', class_='_1047lqyg')
        job['title'] = title_elem.text.strip() if title_elem else 'N/A'

        # Extract company name
        company_elem = article.find('a', class_='_1i4qus51')
        job['company'] = company_elem.text.strip() if company_elem else 'N/A'

        # Extract location
        location_elem = article.find('span', {'data-automation': 'jobCardLocation'})
        job['location'] = location_elem.text.strip() if location_elem else 'N/A'

        # Extract salary (if available)
        salary_elem = article.find('span', {'data-automation': 'jobSalary'})
        job['salary'] = salary_elem.text.strip() if salary_elem else 'N/A'

        # Extract job classification
        classification_elem = article.find('a', {'data-automation': 'jobClassification'})
        if classification_elem:
            job['classification'] = classification_elem.text.strip().strip('()')
        else:
            job['classification'] = 'N/A'

        # Extract posting date information
        date_elem = article.find('span', {'data-automation': 'jobListingDate'})
        job['posting_age'] = date_elem.text.strip() if date_elem else 'N/A'

        # Extract short description (including bullet points)
        description_elems = article.find_all('li', class_='onhoxh6m')
        description = []
        for elem in description_elems:
            desc_text = elem.find('span', class_='_1rhqcq74')
            if desc_text:
                description.append(desc_text.text.strip())

        # Add the main short description
        main_desc_elem = article.find('span', {'data-automation': 'jobShortDescription'})
        if main_desc_elem:
            description.append(main_desc_elem.text.strip())

        job['short_description'] = ' | '.join(description)

        # Extract job URL
        job_url_elem = article.find('a', class_='_1047lqyg')
        if job_url_elem:
            full_url = f"https://www.seek.com.au{job_url_elem['href']}"
            job['url'] = full_url.split('?')[0]  # Remove everything after the '?'
        else:
            job['url'] = 'N/A'

        job_listings.append(job)

    return job_listings

def calculate_post_date(posting_age):
    today = datetime.date.today()
    if posting_age == 'N/A':
        return today.strftime('%Y-%m-%d')

    number = ''.join(filter(str.isdigit, posting_age))
    if number:
        if 'h' in posting_age.lower():  # Check if the posting age is in hours
            return today.strftime('%Y-%m-%d')
        else:
            days_ago = int(number)
            post_date = today - datetime.timedelta(days=days_ago)
            return post_date.strftime('%Y-%m-%d')
    else:
        return today.strftime('%Y-%m-%d')

def scrape_job_title(job_title):
    # Construct the base URL
    job_title_url = job_title.replace(" ", "-")
    base_url = f"https://www.seek.com.au/{job_title_url}-jobs"

    # Add location if provided
    if LOCATION:
        location_url = LOCATION.replace(" ", "-")
        base_url += f"/in-{location_url}"

    # Add a question mark to separate query parameters
    base_url += "?"

    # Add salary range and type if both are provided
    if SALARY_RANGE and SALARY_TYPE:
        base_url += f"salaryrange={SALARY_RANGE}&salarytype={SALARY_TYPE}&"

    # Remove the trailing '&' or '?' if present
    base_url = base_url.rstrip('&?')

    print(f"Base URL for {job_title}: {base_url}")

    all_job_listings = []

    # Scrape pages
    for page in range(1, PAGES_TO_SEARCH + 1):
        url = f"{base_url}&page={page}" if '?' in base_url else f"{base_url}?page={page}"
        print(f"Scraping page {page} for {job_title}...")

        html_content = get_html(url)

        if html_content:
            job_listings = parse_job_listings(html_content)
            all_job_listings.extend(job_listings)
            print(f"Found {len(job_listings)} jobs on page {page}")
        else:
            print(f"Failed to retrieve HTML content for page {page}")

        # Add a delay to avoid overloading the server
        time.sleep(SLEEP_TIME)

    return all_job_listings

def create_connection():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        print(f"Error while connecting to MySQL: {e}")
    return None

def create_table(connection, table_name):
    try:
        with connection.cursor() as cursor:
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255),
                company VARCHAR(255),
                location VARCHAR(255),
                salary VARCHAR(255),
                classification VARCHAR(255),
                short_description TEXT,
                url VARCHAR(255) UNIQUE,
                posting_age VARCHAR(50),
                post_date DATE
            )
            """
            cursor.execute(create_table_query)
        connection.commit()
    except pymysql.Error as e:
        print(f"Error creating table: {e}")

def insert_data(connection, table_name, data):
    try:
        with connection.cursor() as cursor:
            insert_query = f"""
            INSERT INTO {table_name} 
            (title, company, location, salary, classification, short_description, url, posting_age, post_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            title=VALUES(title), company=VALUES(company), location=VALUES(location),
            salary=VALUES(salary), classification=VALUES(classification), 
            short_description=VALUES(short_description), posting_age=VALUES(posting_age),
            post_date=VALUES(post_date)
            """
            cursor.executemany(insert_query, data)
        connection.commit()
        print(f"Inserted/Updated {cursor.rowcount} rows in {table_name}")
    except pymysql.Error as e:
        print(f"Error inserting data: {e}")

# Main execution
connection = create_connection()
if connection is None:
    print("Failed to connect to the database. Exiting.")
    exit(1)

try:
    for job_title in JOB_TITLES:
        print(f"\nScraping data for {job_title}")
        job_listings = scrape_job_title(job_title)

        if job_listings:
            df = pd.DataFrame(job_listings)

            # Calculate post dates
            df['post_date'] = df['posting_age'].apply(calculate_post_date)

            # Remove duplicates based on URL
            df_no_duplicates = df.drop_duplicates(subset=['url'], keep='first')

            # Reorder columns to include new fields
            columns_order = ['title', 'company', 'location', 'salary', 'classification', 'short_description', 'url',
                             'posting_age', 'post_date']
            df_no_duplicates = df_no_duplicates[columns_order]

            # Create table name (replace spaces with underscores and make lowercase)
            table_name = f"{job_title.replace(' ', '_').lower()}_jobs"

            # Create table in the database
            create_table(connection, table_name)

            # Insert data into the database
            data_to_insert = df_no_duplicates.values.tolist()
            insert_data(connection, table_name, data_to_insert)

            print(f"Total jobs scraped for {job_title}: {len(job_listings)}")
            print(f"Total unique jobs after removing duplicates: {len(df_no_duplicates)}")
        else:
            print(f"No job listings found for {job_title}.")

    print("\nScraping completed for all job titles.")

finally:
    # Close the database connection
    connection.close()
    print("Database connection closed.")