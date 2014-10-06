#!/usr/bin/env python3.3-sp

# imports
import app as app_module
import logging, os, sys, time, subprocess, shutil, tarfile, __main__
from pwd import getpwnam

# should check for required enviroment variables here?

def make_tarfile(output_filename, source_dir):
	with tarfile.open(output_filename, "w:gz") as tar:
		tar.add(source_dir, arcname=os.path.basename(source_dir))

def get_backup_path(username, appname):
	path = '/srv/users/{}/backups/{}'.format(username, appname)
	return path

def _chown(path, uid, gid):
	os.chown(path, uid, gid)
	
	for item in os.listdir(path):
		itempath = os.path.join(path, item)
		
		if os.path.isfile(itempath):
			os.chown(itempath, uid, gid)
		elif os.path.isdir(itempath):
			os.chown(itempath, uid, gid)
			_chown(itempath, uid, gid)

def backup_all():
	users = app_module.get_sysusers()
	apps = app_module.get_apps()
	databases = app_module.get_databases()
	
	for app in apps:
		if 'serverid' in os.environ and app['serverid'] == os.environ['serverid'] :
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
			_backup_app(app)

def backup_app(appid):
	# get app
	try:
		app = app_module.get_app(appid)
	except OSError:
		logging.info('Could not get app with id: {}'.format(appid))
		return
	
	# check this app is on this server
	if 'serverid' in os.environ and app['serverid'] != os.environ['serverid'] :
		logging.info('App not on this server: {}'.format(appid))
		return
	
	# get user
	try:
		user = app_module.get_sysuser(app['sysuserid'])
		app['sysuser'] = user
	except OSError:
		logging.info('Could not get user with id: {}'.format(app['sysuserid']))
		return
	
	# get databases
	try:
		databases = app_module.get_databases(appid)
		app['databases'] = databases
	except OSError:
		logging.info('Could not get databases for app {}'.format(appid))
		return
		
	_backup_app(app)

def _backup_app(app):
	# get a timestamp for the directory
	dirstamp = time.strftime('%Y-%m-%d-%I:%M')
	
	#define paths
	app_path = app_module.get_app_path(app['sysuser']['name'], app['name'])
	backups_path = get_backup_path(app['sysuser']['name'], app['name'])
	backup_path = backups_path + '/' + dirstamp
	log_path = backup_path + '/backup.log'
	
	# setup logging
	logging.basicConfig(format='%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename=log_path,level=logging.INFO)
	
	logging.info('Backing up \'{}\' (id: {}) into {}'.format(app['name'], app['id'], backup_path))
	
	logging.info('Log being saved to {}'.format(log_path))
	
	# ensure we have a backup directory
	try:
		os.makedirs( backup_path, 0o755 )
		
		# ensure correct ownership of 'backups'
		_chown(backups_path, getpwnam('root').pw_uid, getpwnam(app['sysuser']['name']).pw_gid)
	except OSError:
		pass
	
	# backup databases
	if len(app['databases']):
		logging.info('Dumping databases... ')
		for db in app['databases']:
			database = db['name']
			try:
				filename = backup_path + '/' + database + '.sql.gz'
				cmd = 'mysqldump {} | gzip > {}'.format(database, filename)
				subprocess.call(cmd, shell=True)
				logging.info('\'{}\' backed up.'.format(database))
			except OSError:
				logging.info('\'{}\' failed to back up.'.format(database))
	else:
		logging.info('No databases found.')
		
	# backup files
	# tar the public directory
	tarfilepath = backup_path + '/app.tar.gz'
	logging.info('Compressing app directory to {}... '.format(tarfilepath))
	make_tarfile(tarfilepath, app_path)
	
	# change ownership
	logging.info('Changing ownership... ')
	_chown(backups_path, getpwnam(app['sysuser']['name']).pw_uid, getpwnam(app['sysuser']['name']).pw_gid)
	
	# delete old backups
	logging.info('Deleting old backups... ')
	
	numdays = 2 * 24 * 60 * 60#seconds
	now = time.time()
	for r,d,f in os.walk(backups_path):
		for dir in d:
			timestamp = os.path.getmtime(os.path.join(r,dir))
			if now-numdays > timestamp and r == backups_path:
				try:
					shutil.rmtree(os.path.join(r,dir))
					logging.info('Deleting {}...'.format(os.path.join(r,dir)))
				except Exception:
					pass
	
	logging.info('Backing up \'{}\' (id: {}) complete.'.format(app['name'], app['id']))