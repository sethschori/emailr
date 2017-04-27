__author__ = 'Seth Schori'

import datetime
import pytz

fmt = '%Y-%m-%d %H:%M:%S %Z%z'

def find_next_local_event(local_timezone, target_weekday, hour, minute):
    utc = pytz.utc
    local_timezone = pytz.timezone(local_timezone)
    utc_now = utc.localize(datetime.datetime.utcnow())
    local_now = utc_now.astimezone(local_timezone)
    return local_now


print(datetime.datetime.utcnow())
print(find_next_local_event('US/Eastern', "Sunday",15, 0))