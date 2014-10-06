#!/usr/bin/env python3.3-sp
#

# import modules used here -- sys is a very standard one
import sys, argparse, logging, os, sp.app, sp.backup
#from sp import app

# functions, classes, globals here
# basically, only put stuff here that is needed when this file is used directly or included in an external file


class SetEnv(argparse.Action):
	def __init__(
		self,
		option_strings,
		dest,
		nargs=None,
		const=None,
		default=None,
		type=None,
		choices=None,
		required=False,
		help=None,
		metavar=None
	):
		argparse.Action.__init__(
			self,
			option_strings=option_strings,
			dest=dest,
			nargs=nargs,
			const=const,
			default=default,
			type=type,
			choices=choices,
			required=required,
			help=help,
			metavar=metavar,
		)
	
	def __call__(self, parser, namespace, values, option_string=None):
		os.environ[self.dest] = values
		
		# Save the results in the namespace using the destination
        # variable given to our constructor.
		setattr(namespace, self.dest, values)

# actions
class BackupAction:
	def __init__(self, args):
		# validate args
		if not args.serverid:
			__main__.backup_parser.error('You must pass a server id using --serverid.')
			
		if not args.appid and not args.all:
			__main__.backup_parser.error('You must specify app ids or pass --all.')
		
		# all, or select?
		if args.all is True:
			sp.backup.backup_all()
			pass
		else:
			for id in args.appid:
				sp.backup.backup_app(id)

# the program.
# put code in here if it should only be used when called directly
if __name__ == '__main__':
	# set logger
	log = logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

	# set parser
	parser = argparse.ArgumentParser(
		description = "ServerPilot command-line tools.",
		epilog = "As an alternative to the command-line, params can be placed in a file, one per line, and specified on the command-line like '%(prog)s @params.conf'.",
		fromfile_prefix_chars = '@'
	)
	
	# generic arguments
	parser.add_argument(
		"-v",
		"--verbose",
		help="increase output verbosity",
		action="store_true"
	)
	
	parser.add_argument(
		"--serverid",
		help="set server id",
		action=SetEnv
	)
	
	parser.add_argument(
		"--clientid",
		help="set client id",
		required=True,
		action=SetEnv
	)
	
	parser.add_argument(
		"--apikey",
		help="set API key",
		required=True,
		action=SetEnv
	)
	
	parser.add_argument(
		"--apiurl",
		help="set API URL",
		action=SetEnv
	)
	
	# SP arguments
	subparsers = parser.add_subparsers(
		#description="Available Resources",
		title="resources",
		metavar="[server|sysuser|app|db]"
	)
	
	# servers
	#server = subparsers.add_parser('server')
	
	# sysusers
	#sysuser = subparsers.add_parser('sysuser')
	
	# apps
	app_parser = subparsers.add_parser('app')
	
	# app methods
	appresources = app_parser.add_subparsers()
	
	# list resource
	list_parser = appresources.add_parser('list')
	
	# all
	list_parser.add_argument(
		"--all",
		help="List all apps.",
		action='store_true',
		#dest="appid"
	)
	
	# by id
	list_parser.add_argument(
		"appid",
		#default="all",
		#nargs='?',#not required
		#nargs='+',#can accept many
		nargs='*',#anything: none, 1, many
		help="List specific apps.",
		#action=ListAppAction
	)
	
	# backup resource
	backup_parser = appresources.add_parser('backup')
	
	# all
	backup_parser.add_argument(
		"--all",
		help="Backup all apps.",
		action='store_true',
		#dest="appid"
	)
	
	# by id
	backup_parser.add_argument(
		"appid",
		#nargs='?',#not required
		#nargs='+',#can accept many
		nargs='*',#anything: none, 1, many
		help="Backup specific apps."
	)
	
	backup_parser.set_defaults(
		action=BackupAction
	)
	
	# dbs
	#db = subparsers.add_parser('db')

	# ... and parse
	args = parser.parse_args()
	
	if hasattr(args, 'action'):
		args.action(args)
	
	# Setup logging
	#if args.verbose:
	#	log.setLevel(logging.DEBUG)