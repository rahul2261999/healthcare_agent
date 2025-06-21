from datetime import datetime
import pytz

def get_current_datetime_in_ist():
  return datetime.now(pytz.timezone('Asia/Kolkata'))