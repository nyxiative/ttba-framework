# This is used for the windows VT1000 workaround
from os import system 
# This is used for parsing the game text files into data that the interpreter 
# can understand
import yaml 
# This makes sure that the text that gets output is automatically wrapped to 
# to multiple lines if the string is too long
import textwrap
# This allows us to use arguments specified when laucnhing the script to load the game
from sys import argv

# Some general global variables for storing game data
game = {}
location = {}
triggers = {'end': False}

# Load the game from a yaml file to a python data structure
def load(filename):
	with open(filename, 'r') as f:
		# Load the file and crash if the file is incorrectly formatted
		try:
			return yaml.safe_load(f)
		except yaml.YAMLError as exc:
			print(exc)
			exit(1)

# This get the part of the game object that represents the location the player 
# is currently located at
# The format that is used in the game file is "location/room"
def parse_location(string):
	parts = string.split('/')
	return game['locations'][parts[0]]['rooms'][parts[1]]

def main():
	global game
	global location
	global triggers

	# Start a new command prompt proccess which enables VT1000 mode and by 
	# extenstion ANSI escape sequences, the fact that VT1000 mode is enabled 
	# after the proccess ends is a bug and shouldn't be relied on, but this is 
	# the easiest way.
	system('')
	# Load the game into the global game variable and parse the starting 
	# location
	game = load(argv[1])
	location = parse_location(game['start'])

	# Print the title of the game and the text of the starting location
	print(f"\u001b[32;1mThe name is the loaded game is '{game['name']}'\u001b[0m")
	print('\u001b[32m', end='')
	print(textwrap.fill(location['message']))

	# The main game loop will run until the end trigger has been set to true
	while True:
		if triggers['end'] == True:
			return

		cmd = input('\u001b[33mWhat would you like to do? \u001b[0m').lower()
		print('\u001b[32m', end='')

		loc = get_exit_from_input(cmd)
		if loc is not None:
			if isinstance(loc, str):
				location = parse_location(loc)
				print(textwrap.fill(location['message']))
				if loc == game['end']:
					return
			else:
				if 'if' in loc:
					printed = False
					for i in loc['if']:
						if i in triggers:
							if triggers[i] == True:
								if '/' in loc['if'][i]:
									location = parse_location(loc['if'][i])
									print(textwrap.fill(location['message']))
									if loc == game['end']:
										return
									printed = True
									break;
								else:
									print(textwrap.fill(loc['if'][i]))
									printed = True
									break;
					if printed == False:
						if '/' in loc['else']:
							location = parse_location(loc['else'])
							print(textwrap.fill(location['message']))
							if loc == game['end']:
										return
						else:
							print(textwrap.fill(loc['else']))
				else:
					print("ERR: Please format correctly")
		else:
			object = get_object_from_input(cmd)
			if object is not None:
				action = get_action_from_input(cmd, object)
				if action is not None:
					val = location['objects'][object]['actions'][action]
					if isinstance(val, str):
						print(textwrap.fill(val))
					else:
						if 'trigger' in val:
							set_triggers(val['trigger'])
						if 'message' in val:
							print(textwrap.fill(val['message']))
							# This is a huge mess but im not sure how to better do it
						elif 'if' in val:
							printed = False
							for condition in val['if']:
								triggered = False
								conditions, typ = parse_condition(condition)
								if typ == "&&":
									for cond in conditions:
										if cond[0] == '!':
											if cond[1:] in triggers:
												if triggers[cond[1:]] == True:
													triggered = True
													break
											else:
												triggered = True
										else:
											if cond in triggers:
												if triggers[cond] == False:
													triggered = True
													break
											else:
												triggered = True
									if triggered == False:
										if isinstance(val['if'][condition], str):
											print(textwrap.fill(val['if'][condition]))
										else:
											set_triggers(val['if'][condition]['trigger'])
											print(textwrap.fill(val['if'][condition]['message']))
										printed = True
										break
								if typ == "||":
									for cond in conditions:
										if cond[0] == '!':
											if cond[1:] in triggers:
												if triggers[cond[1:]] == True:
													if isinstance(val['if'][condition], str):
														print(textwrap.fill(val['if'][condition]))
													else:
														set_triggers(val['if'][condition]['trigger'])
														print(textwrap.fill(val['if'][condition]['message']))
													printed = True
													break
										else:
											if cond in triggers:
												if triggers[cond] == True:
													if isinstance(val['else'], str):
														print(textwrap.fill(val['else']))
													else:
														set_triggers(val['else']['trigger'])
														print(textwrap.fill(val['else']['message']))
													printed = True
													break
								if printed:
									break
							if not printed:
								if isinstance(val['else'], str):
									print(textwrap.fill(val['else']))
								else:
									set_triggers(val['else']['trigger'])
									print(textwrap.fill(val['else']['message']))
						else:
							print('ERROR WRONGLY FORMATTED GAME FILE')
							return
				else:
					print('\u001b[31mSorry you can\'t do that')
			else:
				print('\u001b[31mI don\'t know what you are referring to')


def set_triggers(values):
	if isinstance(values, str):
		if values[0] == '!':
			triggers[values] = False
		else:
			triggers[values] = True
	else:
		for trigger in values:
			if trigger[0] == '!':
				triggers[trigger[1:]] = False
			else:
				triggers[trigger] = True

# Parse condition from string to multiple triggers
# typ is either or or and, and denotes whether the triggers need to all be fufilled or just one
# String representation would look like "&& TRIGGER TRIGGER TRIGGER" or "TRIGGER"
# First two characters are the type of condition and then follows a space seperated list of conditions unless its a single condition
def parse_condition(condition):
	res = condition.split(' ')
	val = (res[1:], res[0]) if len(res) != 1 else (res, "&&")
	return val

# These 3 functions gets either an object, an action, or an exit based on the 
# command and which location you are in

def get_object_from_input(cmd):
	for i in location['objects']:
		names = get_name_and_alias(location['objects'][i], i)
		for name in names:
			if name in cmd:
				return i.replace(' ', '_')

def get_action_from_input(cmd, object):
	for i in location['objects'][object]['actions']:
		names = get_name_and_alias(location['objects'][object]['actions'][i], i)
		for name in names:
			if name in cmd:
				return i.replace(' ', '_')

def get_exit_from_input(cmd):
	for i in location['exits']:
		names = get_name_and_alias(location['exits'][i], i)
		for name in names:
			if name in cmd:
				return location['exits'][i.replace(' ', '_')]
	
# This gets the name and aliases of the object as a list of strings
def get_name_and_alias(obj, name):
	if not isinstance(obj, str):
		if 'alias' in obj:
			return [name.replace('_', ' ')] + list(map(lambda x: x.replace('_', ' '), obj['alias']))
	return [name.replace('_', ' ')]

if __name__ == '__main__':
	main()
