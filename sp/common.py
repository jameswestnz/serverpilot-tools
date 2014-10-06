#!/usr/bin/env python3.3-sp

# imports
import os
import urllib.error
import urllib.request
from urllib.request import urlopen
import json
import setproctitle
import subprocess
import base64

# should check for required enviroment variables here?

# methods
def api_request(api_path, data=None):
	headers = {}
	if data is not None:
		data = json.dumps(data).encode()
		headers['Content-Type'] = 'application/json'
	authval = '{}:{}'.format(os.environ['clientid'], os.environ['apikey'])
	b64authval = base64.b64encode(authval.encode()).decode()
	headers['Authorization'] = 'Basic {}'.format(b64authval)
	request = urllib.request.Request('https://api.serverpilot.io/v1' + api_path, data, headers)
	resp = urlopen(request)
	content = resp.read().decode('utf-8')
	data = json.loads(content)
	return data['data']