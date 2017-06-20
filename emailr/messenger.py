from datetime import timedelta, datetime
from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sys import exc_info
from emailr.models import Event
from emailr.messenger_config import EMAIL_SERVER, SENDER, USERNAME, PASSWORD


engine = create_engine('sqlite:///../emailr.db', convert_unicode=True)
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


def send_message(reminder):
    """Sends email for the reminder object passed to it."""

    destination = reminder.user.email

    # typical values for text_subtype are plain, html, xml
    text_subtype = 'plain'

    subject = reminder.subject
    body = 'This is the reminder email you requested.\r\nHave a nice day.'

    try:
        msg = MIMEText(body, text_subtype)
        msg['Subject'] = subject
        msg['From'] = SENDER
        msg['To'] = reminder.user.email

        conn = SMTP(EMAIL_SERVER)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)

        try:
            conn.sendmail(SENDER, destination, msg.as_string())
            update_next_utc(reminder)

        finally:
            conn.quit()

    except:
        _, err, _ = exc_info()
        print('email error:', err)


def handle_pending():
    """Finds pending reminders and sends them to send_message()."""

    now = datetime.utcnow() + timedelta(seconds=1)
    reminders = db_session.query(Event).filter(Event.next_utc < now)

    for reminder in reminders:
        send_message(reminder)


handle_pending()
