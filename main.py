from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
from flask import jsonify

# Defined in this project
from job_template_sender.sender import send_job_templates
from incoming_pay_estimator.estimator import estimate_pay
from wyzant.session_manager import get_wyzant_session
from google_workspace.authorizer import get_calendar_service

google_service = get_calendar_service()
wyzant_session = get_wyzant_session()

app = Flask(__name__)

# Send job templates once before sending only every ten minutes
send_job_templates(wyzant_session)

# Function to run every 10 minutes
def scheduled_job():
    print("Running scheduled job...")
    send_job_templates(wyzant_session)


# Set up the scheduler
scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=scheduled_job,
    trigger=IntervalTrigger(minutes=10),
    id='send_job_templates_job',
    name='Send job templates every 10 minutes',
    replace_existing=True
)

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Endpoint for triggering function to estimate upcoming pay according to Google Calendar, student rates from Wyzant
# Currently only prints result in log; could send result via telegram as job_template_sender does
# or be delivered to user another way
@app.route('/estimate', methods=['GET'])
def estimate():
    estimate_pay(google_service, wyzant_session)
    return jsonify({'status': 'success'})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)