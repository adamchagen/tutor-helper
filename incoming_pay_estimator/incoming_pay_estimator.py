from datetime import datetime, timedelta
from google_workspace import auth
from dotenv import load_dotenv
import os
from dateutil import parser
from bs4 import BeautifulSoup
import psycopg2
from wyzant.wyzant_login import wyzant_login

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
        print("Accessing Wyzant rates page")
        session = wyzant_login()

        jobs_content = session.get('https://www.wyzant.com/tutor/students').text

        soup = BeautifulSoup(jobs_content, 'lxml')

        tr_list = soup.find_all('tr')

        # Trim the column headers
        tr_list = tr_list[1:]

        for tr in tr_list:
            td_list = tr.find_all('td')
            name_td = td_list[0]
            name = name_td.find('a').text

            # Find the text after the <br> tag
            # First, find the <br> tag
            #br_tag = name_td.find('br')

            # Get the text immediately following the <br> tag
            #location = br_tag.find_next_sibling(string=True).strip()
            #print(location)

            # get payrate for student from Wyzant to insert it
            payrate_td = td_list[3]
            payrate = payrate_td.text.strip()[1:7]

            cur.execute("""
                                SELECT *
                                FROM students
                                WHERE name = %s
                                LIMIT 1;
                            """, (name,))

            result = cur.fetchone()

            if result:
                # Update updated_at
                cur.execute("""
                        UPDATE students
                        SET updated_at = CURRENT_TIMESTAMP,
                        SET payrate = %s
                        WHERE name = %s;
                        """, (payrate, name))

            if not result:
                cur.execute("""
                        INSERT INTO students (name, payrate, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP);
                        """, (name, payrate))

        conn.commit()

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST')
    )

    cur = conn.cursor()

    CALENDAR_ID = os.getenv('CALENDAR_ID')

    beginning = datetime.now()

    end = beginning + timedelta(days=7)

    events_result = service.events().list(
        calendarId=CALENDAR_ID, timeMin=beginning.isoformat() + 'Z',
        maxResults=1000, timeMax=end.isoformat() + 'Z', singleEvents=True,
        orderBy='startTime').execute()
    calendar_events = events_result.get('items', [])

    if not calendar_events:
        print('No upcoming events found.')
        return

    results_updated = False

    is_tutoring_event = lambda item: ':' in item['summary']

    tutoring_events = filter(is_tutoring_event, calendar_events)

    if not tutoring_events:
        print('No upcoming tutoring events found.')
        return

    total_time = 0
    pay = 0

    for event in tutoring_events:
        try:
            color = event['colorId']
        except:
            color = '10'
        if color == '10':
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            new_start = parser.isoparse(start)  # changing the start time to datetime format
            new_end = parser.isoparse(end)  # changing the end time to datetime format
            duration = float(((new_end - new_start)).seconds) / 3600

            event_title = event['summary']
            name = event_title.split(':')[0]

            cur.execute("""
                                SELECT payrate, updated_at
                                FROM students
                                WHERE name = %s
                                LIMIT 1;
                            """, (name,))

            result = cur.fetchone()

            #update/add all student payrates if student is absent or last updated ~2+ months ago
            if not result or result[1] < (datetime.now() - timedelta(days=60)):
                print(result) if result else "f{name} not in database"
                if not results_updated:
                    write_student_rates_to_csv()

                else:
                    print(f"{name} not in database")
                results_updated = True

            total_time += duration
            print(f"Found session with {name} with a duration of {duration} hour(s)")

            cur.execute("""
                    SELECT payrate
                    FROM students
                    WHERE name = %s;
            """, (name,))

            pay += duration * float(cur.fetchone()[0]) * .75

    print(f"Pay: ${pay}")

if __name__ =='__main__':
    service = auth.get_calendar_service()
    incoming_pay_estimator(service)