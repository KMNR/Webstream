import urllib2
import urllib
import simplejson as json
import base64
from secret import *

BLACKLIST = ['Global']

STATUS_PAGE = "http://marconi.kmnr.org:7000/status2.xsl"
METADATA_TARGET = "http://marconi.kmnr.org:7000/admin/metadata.xsl"

ENABLE_LOGGLY = True
#LOGGLY_TARGET = SET ME

#LISTENER_TARGET = SET ME

#METADATA_USER = SET ME
#METADATA_PASS = SET ME

def get_data():
    f = urllib2.urlopen(STATUS_PAGE)
    data = f.read()
    cleaned = data.split('\n')
    f.close()
    return "\n".join(cleaned[2:])

def push_data(status_data):
    data = {'data':status_data}
    qs = urllib.urlencode(data)
    req = urllib2.Request(LISTENER_TARGET,qs)
    f = urllib2.urlopen(req)
    r = f.read().strip()
    f.close()
    return r.replace("\"","'")

def push_data_loggly(status_data):
    header = {'content-type': 'application/json'}
    req = urllib2.Request(LOGGLY_TARGET,status_data,header)
    f = urllib2.urlopen(req)
    r = f.read().strip()
    f.close()

def push_metadata(status_data, show_data):
    data = json.loads(status_data)
    for mp in data['MountPoints']:
        try:
            if mp['MountPoint'] in BLACKLIST:
                continue
            path = mp['MountPoint']
        except KeyError:
            continue
        query = {'song':show_data,
                 'mount':path,
                 'mode':"updinfo",
                 'charset':"UTF-8"}
        qs = urllib.urlencode(query)
        url = METADATA_TARGET + "?" + qs
        req = urllib2.Request(url)
        up = base64.encodestring('%s:%s' % (METADATA_USER,METADATA_PASS)).replace('\n','')
        req.add_header("Authorization","Basic %s" % up)
        f = urllib2.urlopen(req)
        f.close()

if __name__ == "__main__":
    status_data = get_data()
    if ENABLE_LOGGLY:
        push_data_loggly(status_data)
    show_string = push_data(status_data)
    push_metadata(status_data,show_string)
    
