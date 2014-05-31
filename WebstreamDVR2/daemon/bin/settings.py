from datetime import timedelta

SCHEDULE_URL = "http://kmnr.org/api/schedule/"
RIPPER_COMMAND = "icecream --name='{target}{show}/{show}-%Y-%m-%d' --stop='{duration}min' -q {stream}"
