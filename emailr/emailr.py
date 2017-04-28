__author__ = 'Seth Schori'

from datetime import datetime, timedelta
import pytz
import sqlalchemy

fmt = '%Y-%m-%d %H:%M:%S %Z%z'

def day_text_to_int(weekday):
    # Given the string of a weekday, return the datetime integer.
    # Python's datetime format for weekdays is: Monday = 0, Sunday = 6
    WEEKDAYS = ['monday',
                'tuesday',
                'wednesday',
                'thursday',
                'friday',
                'saturday',
                'sunday']
    return WEEKDAYS.index(weekday.lower())

def find_next_occur(local_tz, target_weekday, target_hour, target_min):
    # Returns the UTC equivalent of when the next target weekday and time
    # combination will occur in a given local timezone.
    #
    # INPUTS:
    #   local_tz: Olson tz string (e.g. 'US/Eastern' or 'Asia/Tokyo')
    #   target_weekday: weekday string (e.g. 'Sunday')
    #   target_hour: int from 0 to 23
    #   target_min: int from 0 to 59
    #
    # OUTPUT:
    #   date and time as a pytz object in local timezone

    # Store the current, pytz-localized datetime value of UTC time.
    utc_now = pytz.utc.localize(datetime.utcnow())

    # Convert target_weekday from a string to an int
    target_weekday = day_text_to_int(target_weekday)

    # Convert local_tz from a string to a pytz timezone
    local_tz = pytz.timezone(local_tz)

    # Determine the current date and time in the local timezone.
    local_now = utc_now.astimezone(local_tz)

    # Determine the current weekday in the local timezone.
    local_now_weekday = local_now.weekday()

    # Figure out when the next occurrence of the target weekday will be,
    # depending on whether the target weekday is before, after, or the same
    # as the current weekday.
    if target_weekday > local_now_weekday:  # target is after local weekday
        days_diff = target_weekday - local_now_weekday
    elif target_weekday < local_now_weekday:  # target is before local weekday
        days_diff = 7 - local_now_weekday + target_weekday
    else:
        # When target weekday is the same as local weekday, we need to
        # determine whether the target time is before or after the local time.
        test_dt = local_tz.localize(datetime(local_now.year, local_now.month,
                                             local_now.day, target_hour,
                                             target_min, 0))
        '''
            Improve the line below so that testing for 5 minutes after now.
        '''
        if test_dt > local_now:
            days_diff = 0
        else:
            days_diff = 7

    # By computing in local time and localizing to UTC, this approach avoids
    # daylight savings time problems. If the next occurrence will take place
    # during the "impossible" 2:00 spring-ahead hour, it gets scheduled an
    # hour later. If the next occurrence will take place during the 1:00
    # fall-back hour, it gets scheduled during the second "repeat" hour.

    target_date = local_now + timedelta(days=days_diff)
    target_date = local_tz.localize(datetime(target_date.year,
                                             target_date.month,
                                             target_date.day, target_hour,
                                             target_min, 0))
    target_date = target_date.astimezone(pytz.utc)

    return target_date


test = find_next_occur('America/New_York', "Friday", 1, 1)

