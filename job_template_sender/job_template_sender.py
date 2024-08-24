import dotenv
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
import re
from datetime import datetime
from wyzant.wyzant_login import wyzant_login

load_dotenv()

def get_template(subject: str, name: str, start: str, son_daughter_myself: str):
    pattern = r'(\w+), (\w+) (\d+), (\d{4}) at (\d{1,2}:\d{2} [APM]{2}) ([A-Z]{3,4})'
    match = re.search(pattern, start)

    #create datetime of student's desired start
    if match:
        weekday_name, month_name, day, year, time_str, timezone = match.groups()

        date_str = f"{month_name} {day}, {year}"
        print(date_str)

        date_obj = datetime.strptime(date_str, '%B %d, %Y')
        time_obj = datetime.strptime(time_str, '%I:%M %p').time()
        full_datetime = datetime.combine(date_obj, time_obj)

    #First part depends on whom the tutoring is for
    part1 = (f"Hi {name}, I'd be happy to help you with your {subject}. " if son_daughter_myself == 'myself' else
            f"Hi {name}, I'd be happy to work with your daughter. " if son_daughter_myself == 'daughter' else
            f"Hi {name}, I'd be happy to work with your son. ")

    #Second part depends on what the subject is
    MCAT_MESSAGE = os.getenv('MCAT_MESSAGE')
    CHEMISTRY_MESSAGE = os.getenv('CHEMISTRY_MESSAGE')

    part2 = MCAT_MESSAGE if subject == 'MCAT' else CHEMISTRY_MESSAGE

    return part1 + part2

with open('jobs.html', 'r') as jobs_html:
    jobs_content = jobs_html.read()

#soup = BeautifulSoup(jobs_content, 'lxml')

soup = wyzant_login()

s = requests.session()

for job in soup.find_all('div', class_='row spc-small-ew spc-med-ew'):
    recency = job.find('span', class_='text-semibold text-light').text.strip()

    subject = job.find('a', class_='job-details-link').text.strip()

    name = job.find('p', class_='text-semibold spc-zero-n spc-tiny-s').text.strip()

    description = job.find('p', class_='spc-zero-s job-description').text.strip()

    #search for "Suggested" in the description in reverse to get the suggested first lesson time (start)
    reverse_index = description[::-1].find('Suggested'[::-1])
    index = len(description) - reverse_index - len('Suggested')
    start = description[index:]
    print(start)


    son_daughter_myself = 'myself'
    if description.find('daughter') != -1:
        son_daughter_myself = 'daughter'
    elif description.find(' son') != -1:
        son_daughter_myself = 'son'

    template = get_template(subject, name, start, son_daughter_myself)
    print(template)
    print("")

    TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    s.get(f'https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={template}')