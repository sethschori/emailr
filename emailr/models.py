from datetime import datetime, time, timedelta
import pytz
from sqlalchemy import Boolean, Column, Integer, DateTime, ForeignKey, \
    String, Time
from sqlalchemy.orm import relationship
from emailr.database import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(128), unique=True, nullable=False)
    timezone_str = Column(String(64), nullable=False)
    # hard_bounce = Column(Boolean, nullable=False)
    oauth = Column(String(256))
    events = relationship("Event", backref="user")

    def __init__(self, email, timezone_str):
        self.email = email
        self.timezone_str = timezone_str

    def __repr__(self):
        return "<user {email} {oauth}>".format(email=self.email,
                                               oauth=self.oauth)


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    local_weekday = Column(Integer, nullable=False)
    local_time = Column(Time, nullable=False)
    subject = Column(String(128), nullable=False)
    local_tz = Column(String(128), nullable=False)
    next_utc = Column(DateTime)
    # active = Column(Boolean, nullable=False)  # reinstate later

    def __init__(self, weekday_int, hour_int, min_int, subject, tz, user_id):
        self.user_id = user_id
        self.local_weekday = weekday_int
        self.local_time = time(hour_int, min_int)
        self.subject = subject
        self.local_tz = tz  # NEED TO GET THE USER(ID).TIMEZONE_STR
        self.next_utc = self.find_next_occur()
        # self.next_local = self.next_utc.astimezone(timezone)

    def __repr__(self):
        return "Event({d}, {h}, {m}, {s})".format(
            d=self.local_weekday, h=self.local_time.hour,
            m=self.local_time.minute, s=self.subject)

    def find_next_occur(self):
        """ Returns the UTC equivalent of when the next target weekday and time
        will occur in a given local timezone as a pytz object."""

        # Store the current, pytz-localized datetime value of UTC time.
        utc_now = pytz.utc.localize(datetime.utcnow())

        # Determine the current date and time in the local timezone.
        local_tz_obj = pytz.timezone(self.local_tz)
        local_now = utc_now.astimezone(local_tz_obj)

        # Determine the current weekday in the local timezone.
        local_now_weekday = local_now.weekday()

        # Determine next occurrence of target weekday, depending on whether
        # the target weekday is before, after, or the same as current weekday.
        if self.local_weekday > local_now_weekday:
            days_diff = self.local_weekday - local_now_weekday
        elif self.local_weekday < local_now_weekday:
            days_diff = 7 - local_now_weekday + self.local_weekday
        else:
            # When target weekday is the same as local weekday, determine
            # whether the target time is before or after the local time.
            test_dt = local_tz_obj.localize(datetime(local_now.year,
                                                     local_now.month,
                                                     local_now.day,
                                                     self.local_time.hour,
                                                     self.local_time.minute,
                                                     0))
            '''
                Improve the line below so that testing for 5 minutes after now.
            '''
            if test_dt > local_now:
                days_diff = 0
            else:
                days_diff = 7

        # Computing in local time and localizing to UTC avoids daylight
        # savings time problems. If the next occurrence takes place during
        # the "impossible" 2:00 spring-ahead hour, it gets scheduled an hour
        # later. If the next occurrence will take place during the 1:00
        # fall-back hour, it gets scheduled during the second "repeat" hour.

        target_date = local_now + timedelta(days=days_diff)
        target_date = local_tz_obj.localize(datetime(target_date.year,
                                                     target_date.month,
                                                     target_date.day,
                                                     self.local_time.hour,
                                                     self.local_time.minute,
                                                     0))
        target_date = target_date.astimezone(pytz.utc)

        target_date = datetime(target_date.year, target_date.month,
                               target_date.day, target_date.hour,
                               target_date.minute)

        return target_date
