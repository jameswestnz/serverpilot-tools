serverpilot-client
==================

ServerPilot Python Client

Install into self-contained directory - on a ServerPilot server, try /opt/tools

Create params.conf with the following information:
```
--serverid=SERVER_ID_HERE
--clientid=CLIENT_ID_HERE
--apikey=API_KEY_HERE
```

Usage:
```
./sp.py app backup [--all|appid1,appid2,...]
```

Notes:
- Backups must be run on the host server due to needing access to the database and files.
- The client must be run as root (not sudo) when attempting to run any database-reliant methods.

To-do:
- Lots...
- Logging
- List output types i.e. view all apps in a table or output as json
- Error catching
- Dependancy checking
- Clean code
- Is there a better way to do some of this? Probably - submit a pull request if you write some handy code.