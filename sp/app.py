#!/usr/bin/env python3.3-sp

# imports
import common as common_module
import __main__

def get_sysusers():
	return common_module.api_request('/sysusers')

def get_sysuser(sysuserid):
	return common_module.api_request('/sysusers/{}'.format(sysuserid))

def get_apps():
	return common_module.api_request('/apps')

def get_app(appid):
	return common_module.api_request('/apps/{}'.format(appid))

def get_databases(appid=False):
	dbs = common_module.api_request('/dbs')
	if appid is not False:
		dbs = [ db for db in dbs if db['appid'] == appid ]
	return dbs

def get_app_path(username, appname):
	path = '/srv/users/{}/apps/{}'.format(username, appname)
	return path