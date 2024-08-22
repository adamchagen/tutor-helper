from datetime import datetime, timedelta
from google_workspace import auth
from dotenv import load_dotenv
import os
from dateutil import parser
from bs4 import BeautifulSoup
import psycopg2

"""
To be used later: code for getting all calendar ids
Requires full google calendar scope ('https://www.googleapis.com/auth/calendar')
calendars = service.calendarList().list().execute()

    for calendar in calendars.get('items', []):
        print(f"Calendar Name: {calendar['summary']}, Calendar ID: {calendar['id']}")
"""

load_dotenv()

def incoming_pay_estimator(service):
    def write_student_rates_to_csv():
        with open('student_rates.html', 'r') as jobs_html:
            jobs_content = jobs_html.read()

        soup = BeautifulSoup(jobs_content, 'lxml')

        tr_list = soup.find_all('tr')

        # Trim the column headers
        tr_list = tr_list[1:]

        for tr in tr_list:
            td_list = tr.find_all('td')
            name_td = td_list[0]
            name = name_td.find('a').text
            print(name)

            # Find the text after the <br> tag
            # First, find the <br> tag
            br_tag = name_td.find('br')

            # Get the text immediately following the <br> tag
            location = br_tag.find_next_sibling(string=True).strip()
            print(location)

            cur.execute("""
                                SELECT *
                                FROM students
                                WHERE name = %s
                                LIMIT 1;
                            """, (name, subject))

            result = cur.fetchone()

            if not result:
                # get payrate for student from Wyzant to insert it
                payrate_td = td_list[3]
                payrate = payrate_td.text.strip()[:7]
                print(payrate)

                # Insert the data into the students table
                cur.execute("""
                        INSERT INTO students (name, location, payrate)
                        VALUES (%s, %s, %s);
                        """, (name, location, payrate))
    CALENDAR_ID = os.getenv('CALENDAR_ID')

    beginning = datetime.now()

    end = beginning + timedelta(days=7)

    events_result = service.events().list(
        calendarId=CALENDAR_ID, timeMin=beginning.isoformat() + 'Z',
        maxResults=1000, timeMax=end.isoformat() + 'Z', singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    for event in events:
        try:
            color = event['colorId']
        except:
            color = '10'
        if (color == '10'):
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            new_start = parser.isoparse(start)  # changing the start time to datetime format
            new_end = parser.isoparse(end)  # changing the end time to datetime format
            duration = float(((new_end - new_start)).seconds) / 3600

            event_title = event['summary']
            name = event_title.split(':')[0]

            print(duration)

            conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST')
            )

            cur = conn.cursor()

            cur.execute("""
                                SELECT payrate
                                FROM students
                                WHERE name = %s
                                ORDER BY id DESC
                                LIMIT 1;
                            """, name)

            result = cur.findone()

            if not result:
                write_student_rates_to_csv()


            """
            total_time += duration
            print(event['summary'] + " " + str(duration) + " hours")
            if (color == '5'):
                print("Input travel time")
                duration -= int(input()) / 30
            pay += duration * get_rate(event['summary'])
            """

if __name__ =='__main__':
    service = auth.get_calendar_service()
    incoming_pay_estimator(service)