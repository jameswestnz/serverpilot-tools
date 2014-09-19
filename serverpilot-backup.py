#!/usr/bin/env python3.3-sp

# imports
import base64
import configparser
import logging as log
import os
import sys
import json
import setproctitle
import time
import shutil
import subprocess
import urllib.error
import urllib.request
from urllib.request import urlopen
import tarfile
from pwd import getpwnam

# vars
AGENT_CONF_FILE = '/etc/serverpilot/client.conf'

config = configparser.ConfigParser()

# Set the default configuration that can be overridden through AGENT_CONF_FILE.
config.read_dict({
	'server': {
		'id': '',
		'client_id': '',
		'client_apikey': '',
	},
	'api': {
		'url': 'https://api.serverpilot.io/v1',
		'max_poll_wait_seconds': 60,
		'allow_insecure_https': False
	},
	'log': {
		'file': '/var/log/serverpilot/backup.log'
	},
	'misc': {
		'proctitle': 'sp-backup',
		'pidfile': '/var/run/serverpilot-backup.pid'
	}
})

# import config
config.read([AGENT_CONF_FILE])
if not config['server']['id']:
		log.info('server::id not set in {}'.format(AGENT_CONF_FILE), file=sys.stderr)
		sys.exit(1)
if not config['server']['client_id']:
		log.info('server::client_id not set in {}'.format(AGENT_CONF_FILE), file=sys.stderr)
		sys.exit(1)
if not config['server']['client_apikey']:
		log.info('server::client_apikey not set in {}'.format(AGENT_CONF_FILE), file=sys.stderr)
		sys.exit(1)

# setup logging
log.basicConfig(format='%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename=config['log']['file'],level=log.INFO)

# methods
def api_request(api_path, data=None):
	headers = {}
	if data is not None:
		data = json.dumps(data).encode()
		headers['Content-Type'] = 'application/json'
	authval = '{}:{}'.format(config['server']['client_id'], config['server']['client_apikey'])
	b64authval = base64.b64encode(authval.encode()).decode()
	headers['Authorization'] = 'Basic {}'.format(b64authval)
	return urllib.request.Request(config['api']['url'] + api_path, data, headers)

def make_tarfile(output_filename, source_dir):
	with tarfile.open(output_filename, "w:gz") as tar:
		tar.add(source_dir, arcname=os.path.basename(source_dir))
		
def _chown(path, uid, gid):
	os.chown(path, uid, gid)
	
	for item in os.listdir(path):
		itempath = os.path.join(path, item)
		
		if os.path.isfile(itempath):
			os.chown(itempath, uid, gid)
		elif os.path.isdir(itempath):
			os.chown(itempath, uid, gid)
			_chown(itempath, uid, gid)

def get_sysusers():
	request = api_request('/sysusers')
	resp = urlopen(request)
	content = resp.read().decode('utf-8')
	data = json.loads(content)
	return data['data']

def get_apps():
	request = api_request('/apps')
	resp = urlopen(request)
	content = resp.read().decode('utf-8')
	data = json.loads(content)
	return data['data']

def get_databases():
	request = api_request('/dbs')
	resp = urlopen(request)
	content = resp.read().decode('utf-8')
	data = json.loads(content)
	return data['data']

def get_app_path(username, appname):
	path = '/srv/users/{}/apps/{}'.format(username, appname)
	return path

def get_backup_path(username, appname):
	path = '/srv/users/{}/backups/{}'.format(username, appname)
	return path

def backup_app(app):
	# we'll wait at the start of each backup
	time.sleep(5)
	
	# get a timestamp for the directory
	dirstamp = time.strftime('%Y-%m-%d-%I:%M')
	
	#define paths
	app_path = get_app_path(app['sysuser']['name'], app['name'])
	backups_path = get_backup_path(app['sysuser']['name'], app['name'])
	backup_path = backups_path + '/' + dirstamp
	
	log.info('Backing up app \'{}\' into {}'.format(app['name'], backup_path))
	
	# ensure we have a backup directory
	try:
		os.makedirs(backup_path, 755)
	except OSError:
		pass
	
	# backup databases
	log.info('Dumping databases... ')
	for db in app['databases']:
		database = db['name']
		filename = backup_path + '/' + database + '.sql'
		cmd = 'mysqldump {} > {}'.format(database, filename)
		subprocess.call(cmd, shell=True)
		
	# backup files
	# tar the public directory
	log.info('Compressing app directory... ')
	make_tarfile(backup_path + '/app.tar.gz', app_path)
	
	# change ownership
	log.info('Changing ownership... ')
	_chown(backups_path, getpwnam(app['sysuser']['name']).pw_uid, getpwnam(app['sysuser']['name']).pw_gid)
	
	# delete old backups
	log.info('Deleting old backups... ')
	
	numdays = 2 * 24 * 60 * 60#seconds
	now = time.time()
	for r,d,f in os.walk(backups_path):
		for dir in d:
			timestamp = os.path.getmtime(os.path.join(r,dir))
			if now-numdays > timestamp and r == backups_path:
				try:
					shutil.rmtree(os.path.join(r,dir))
					log.info('Deleting {}...'.format(os.path.join(r,dir)))
				except Exception:
					pass
	
	log.info('Backing up \'{}\' complete.'.format(app['name']))

def backup():
	log.info('Retrieving server app information...')

	users = get_sysusers()
	apps = get_apps()
	databases = get_databases()
	
	log.info('Starting backups...')
	
	for app in apps:
		if(app['serverid'] == config['server']['id']) :
			# attach the user
			for user in users:
				if(user['id'] == app['sysuserid']):
					app['sysuser'] = user
			
			# attach the databases
			app['databases'] = []
			for database in databases:
				if(database['appid'] == app['id']):
					app['databases'].append(database)
			
			# do backupy things here
			backup_app(app)

# runtime
# execute backup method
backup()
