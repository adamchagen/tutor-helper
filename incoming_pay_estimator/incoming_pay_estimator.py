from datetime import datetime, timedelta
from google_workspace import auth
from dotenv import load_dotenv
import os
from dateutil import parser

"""
To be used later: code for getting all calendar ids
Requires full google calendar scope ('https://www.googleapis.com/auth/calendar')
calendars = service.calendarList().list().execute()

    for calendar in calendars.get('items', []):
        print(f"Calendar Name: {calendar['summary']}, Calendar ID: {calendar['id']}")
"""

def incoming_pay_estimator(service):
    load_dotenv()
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

            print(duration)
            """
            total_time += duration
            print(event['summary'] + " " + str(duration) + " hours")
            if (color == '5'):
                print("Input travel time")
                duration -= int(input()) / 30
            pay += duration * get_rate(event['summary'])
            """

def write_student_rates_to_csv(service):
    pass


if __name__ =='__main__':
    service = auth.get_calendar_service()
    incoming_pay_estimator(service)