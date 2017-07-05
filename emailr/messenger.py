from datetime import timedelta, datetime
from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP
from sys import exc_info

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from emailr.models import Event
from emailr.settings.config import DB_USERNAME, DB_PASSWORD, DB_ENDPOINT, \
    DB_DATABASE, EMAIL_SERVER, EMAIL_SENDER, EMAIL_USERNAME, EMAIL_PASSWORD


'''Database model for the application.'''

# The code below was mostly copied from:
# http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/#declarative

# engine = create_engine('sqlite:///emailr.db', convert_unicode=True)
engine = create_engine('postgresql://' + DB_USERNAME + ':' + DB_PASSWORD + '@'
                       + DB_ENDPOINT + '/' + DB_DATABASE,
                       client_encoding='utf8')

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False, bind=engine))


def update_next_utc(event_obj):
    """Updates the next_utc value in the database for the event_obj passed."""

    new_utc = Event(event_obj.local_weekday, event_obj.local_time.hour,
                    event_obj.local_time.minute, event_obj.subject,
                    event_obj.user.timezone_str, event_obj.user.id).next_utc
    target_obj = db_session.query(Event).filter(Event.id == event_obj.id).one()
    target_obj.next_utc = new_utc
    db_session.commit()


def day_int_to_text(weekday):
    # Given the integer of a weekday, return the datetime string.
    weekdays = ['Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday']
    return weekdays[weekday]


def send_message(reminder):
    """Sends email for the reminder object passed to it."""

    destination = reminder.user.email

    # typical values for text_subtype are plain, html, xml
    text_subtype = 'html'

    subject = '[jog.gy] ' + reminder.subject

    local_weekday = day_int_to_text(reminder.local_weekday) + 's'
    local_time = reminder.local_time.strftime("%I:%M %p")

    body_html = '''<html>
        <head>
            <style type="text/css">
                @media screen {{
                    
                    #wrapper {{
                        min-width: 300px;
                        max-width: 600px;
                        font-size: 1em;
                        line-height: 1.7em;
                        background-color: #f5f5f5;
                        padding: 60px;
                    }}
                    
                    p {{
                        color: #555;
                    }}
                    
                    #logo-wrapper {{
                        text-align: center;
                    }}
                    
                    #logo-image {{
                        width: 200px;
                        height: auto;
                    }}
                    
                    a {{
                        text-decoration: none;
                        color: #247ba0;
                    }}
                    
                    a:hover {{
                        text-decoration: underline;
                        text-decoration-style: dotted;
                    }}
                    
                    
                    
                }}
            </style>
        </head>
        <body>
            <div id="wrapper">
                <p id="logo-wrapper"><img 
                src="https://s3.amazonaws.com/jog.gy/img/joggy.png" 
                id="logo-image"></img></p>
                <p>Hi there,</p>
                <p>You requested to have <a style="color: #555">jog.gy</a> 
                send you reminder emails on {d} at {t} with the subject 
                <strong>"{s}"</strong>.</p>
                <p>Have a nice day,
                <br/>Your friends at <a href="http://jog.gy/">jog.gy</a></p>
            </div>
        </body>
    </html>'''.format(d=local_weekday, t=local_time, s=reminder.subject)

    body_text = 'Hi there,\r\nYou requested to have jog.gy send you ' \
                'reminder emails on {d} at {t} with the subject "{s}".\r\n' \
                'So here\'s your reminder.\r\nHave a nice ' \
                'day,\r\nYour friends at jog.gy'.format(d=local_weekday,
                                                        t=local_time,
                                                        s=reminder.subject)

    try:
        msg = MIMEText(body_html, text_subtype)
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = reminder.user.email

        conn = SMTP(EMAIL_SERVER)
        conn.set_debuglevel(False)
        conn.login(EMAIL_USERNAME, EMAIL_PASSWORD)

        try:
            conn.sendmail(EMAIL_SENDER, destination, msg.as_string())
            update_next_utc(reminder)

        finally:
            conn.quit()

    except:
        _, err, _ = exc_info()
        print('email error:', err)


def handle_pending(event, context):
    """Finds pending reminders and sends them to send_message()."""

    now = datetime.utcnow() + timedelta(seconds=1)
    reminders = db_session.query(Event).filter(Event.next_utc < now)

    for reminder in reminders:
        send_message(reminder)


if __name__ == "__main__":
    handle_pending(None, None)
