from datetime import datetime, timedelta
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


def estimate_pay(google_service, wyzant_session):

    # This runs when a student from a google calendar event isn't in the db or their rate was updated 2+ months ago
    def write_student_rates_to_db():
        print("Accessing Wyzant rates page")
        jobs_content = wyzant_session.get('https://www.wyzant.com/tutor/students').text

        soup = BeautifulSoup(jobs_content, 'lxml')

        # Jobs have this tag
        tr_list = soup.find_all('tr')

        # Trim the column headers
        tr_list = tr_list[1:]

        for tr in tr_list:
            # Name, payrate inside td tag
            td_list = tr.find_all('td')
            name_td = td_list[0]

            # Name inside the a tag
            name = name_td.find('a').text

            # Find the text after the <br> tag
            # First, find the <br> tag
            #br_tag = name_td.find('br')

            # Get the text immediately following the <br> tag
            #location = br_tag.find_next_sibling(string=True).strip()
            #print(location)

            # get payrate for student from Wyzant to insert it
            payrate_td = td_list[3]

            # Don't keep '$', extra info after rate
            payrate = payrate_td.text.strip()[1:7]

            # Check if student name exists in db, extract if it does
            cur.execute("""
                                SELECT *
                                FROM students
                                WHERE name = %s
                                LIMIT 1;
                            """, (name,))

            result = cur.fetchone()

            # Update the payrate if student name exists, update 'updated_at' for use when checking if
            # existing rate is too old (see below)
            if result:
                # Update updated_at and payrate
                cur.execute("""
                        UPDATE students
                        SET updated_at = CURRENT_TIMESTAMP,
                            payrate = %s
                        WHERE name = %s;
                        """, (payrate, name))

            if not result:
                # Insert student name, payrate, updated_at in db
                cur.execute("""
                        INSERT INTO students (name, payrate, updated_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP);
                        """, (name, payrate))

        # Commit after all students from page updated
        conn.commit()

    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST')
    )

    cur = conn.cursor()

    CALENDAR_ID = os.getenv('CALENDAR_ID')

    # Only get tutoring events for next week
    beginning = datetime.now()

    end = beginning + timedelta(days=7)

    events_result = google_service.events().list(
        calendarId=CALENDAR_ID, timeMin=beginning.isoformat() + 'Z',
        maxResults=1000, timeMax=end.isoformat() + 'Z', singleEvents=True,
        orderBy='startTime').execute()
    calendar_events = events_result.get('items', [])

    # No events in calendar in next 7 days whatsoever
    if not calendar_events:
        print('No upcoming events found.')
        return

    is_tutoring_event = lambda item: ':' in item['summary']

    tutoring_events = filter(is_tutoring_event, calendar_events)

    if not tutoring_events:
        print('No upcoming tutoring events found.')
        return

    total_time = 0
    pay = 0

    # We'll check every student on google calendar events to see if they're in db and run
    # write_student_rates_to_db if any students or missing or updated 2+ months ago
    # but, we only need to run student_rates_to_db once as it checks all students on Wyzant
    # results_updated should be updated to True 0 or 1 times
    results_updated = False

    for event in tutoring_events:
        # Sage green == student confirmed, other color (e.g., red) = student not confirmed
        # Sage green is the default color for this particular calendar
        # Default color doesn't have 'colorId' value, so we default it to sage green
        try:
            color = event['colorId']
        except:
            color = '10'
        if color == '10':
            # Figure the duration of the event for later use in determining total pay for session
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            new_start = parser.isoparse(start)  # changing the start time to datetime format
            new_end = parser.isoparse(end)  # changing the end time to datetime format
            duration = float(((new_end - new_start)).seconds) / 3600

            # 'summary' is the value for the event title, contains student name and subject in this format:
            # FirstName I.: Subject
            event_title = event['summary']

            # name comes before ':' in above format
            name = event_title.split(':')[0]

            # Get existing student from db with this name
            cur.execute("""
                                SELECT payrate, updated_at
                                FROM students
                                WHERE name = %s
                                LIMIT 1;
                            """, (name,))

            result = cur.fetchone()

            # update/add all student payrates if student is absent or last updated ~2+ months ago
            if not result or result[1] < (datetime.now() - timedelta(days=60)):
                print(result) if result else "f{name} not in database"
                if not results_updated:
                    write_student_rates_to_db()
                    results_updated = True

                # This runs if 1. we have already written students from Wyzant to db and 2. student
                # is still not in the db (i.e., student wasn't found on Wyzant rates page
                else:
                    print(f"{name} not in database")

            # Track total_time in upcoming sessions, not currently used but could be of interest to user
            total_time += duration
            print(f"Found session with {name} with a duration of {duration} hour(s)")

            # After either confirming student is present in db or adding them to db, get their payrate from db
            cur.execute("""
                    SELECT payrate
                    FROM students
                    WHERE name = %s;
            """, (name,))

            # Tutor only sees 75% of total student payrate
            pay += duration * float(cur.fetchone()[0]) * .75

    print(f"Pay: ${pay}")