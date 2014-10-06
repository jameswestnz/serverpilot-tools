import os, sys

# add import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# itterate and import
for module in os.listdir(os.path.dirname(__file__)):
	if module == '__init__.py' or module[-3:] != '.py':
		continue
	__import__(module[:-3], locals(), globals())

# remove imported modules
del os, sys, module