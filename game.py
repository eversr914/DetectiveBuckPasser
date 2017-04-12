import Character
import characters
import Room
import Rooms
import hero
import objects
import userInput
import getpass, readline, click, csv, traceback, numpy, sqlite3, os
import toolBag
import items
import inventory
'''
To do:
1) make a game file directory entry with the current room, etc
2) how to do searches and __getItem?
3) How do we wanna do the clever dialog? do each room have a string of possible exit strings to play?
4) How should conversations with the characters go?
'''
class Game(object):
	'''
	self.currRoom is the room the character is in
	self.inspection is the object, item, room, character that is being looked at. Each of these needs to have a dictionary of possible commands. The games superset of commands always apply.
	Have the user declare that they're done to either go up a layer of inspection or back to the room
	'''
	def __init__(self):
		self.connection = None
		self.dbFile = 'gameDB.db'
		self.currRoom = None
		self.musicProcess = None
		self.inspection = None
		self.buckPasser = None
		self.defaultCommands = {
			'save':userInput.Command(func=self.__save, takesArgs=False, descrip = 'save game'),
			'load':userInput.Command(func=self.__load, takesArgs=True, descrip = 'Load game from an existing save file'),
			'exit':userInput.Command(func=self.__exit, takesArgs=False, descrip = 'Exit game immediately'),
			'move':userInput.Command(func=self.move, takesArgs=True, descrip = 'Move to a neighboring room'),
			'commands':userInput.Command(func=self.printCommands, takesArgs=False, descrip = 'Print the available commands'),
			'help':userInput.Command(func=self.printHelp, takesArgs=False, descrip = 'No one can save you now'),
			'music':userInput.Command(func=self.music, takesArgs=True, descrip = 'Choose some sweet sultry tunes'),
			'mute':userInput.Command(func=self.mute, takesArgs=False, descrip = 'Mute the music', hide = True),
			'use':userInput.Command(func=self.use, takesArgs=True, descrip = 'Use an item', hide = True),
			'describe':userInput.Command(func=self.describe, takesArgs=True, descrip = 'Description of a person or thing', hide = True),
			'grab':userInput.Command(func=self.grab, takesArgs=True, descrip = 'Take an item', hide = True),
			'talk':userInput.Command(func=self.talkTo, takesArgs=True, descrip = 'Really need this fucking explained you dim wit?'),
			'items':userInput.Command(func=self.listItems, takesArgs=True, descrip = 'List what you have on you'),
			'inventory':userInput.Command(func=self.listItems, takesArgs=True, descrip = 'Look at the items you have', hide = True),
			'search':userInput.Command(func=self.search, takesArgs=True, descrip = 'Root around for something')
			}
		self.commands = self.defaultCommands

	def __setupGame(self):
		os.system('sqlite3 {0} < {1}'.format(self.dbFile, 'sqlStructure.sql'))
		self.buckPasser = hero.Hero(self.connection)
		characters.SixDollarMan(self.connection).writeToDB()
		characters.Bear(self.connection).writeToDB()

		Rooms.HomeApt(self.connection).writeToDB()
		Rooms.Apartment_3B(self.connection).writeToDB()
		Rooms.MurderScene(self.connection).writeToDB()

		objects.Couch(self.connection).writeToDB()
		objects.Cushions(self.connection).writeToDB()
		objects.Feathers(self.connection).writeToDB()
		objects.Computer(self.connection).writeToDB()

		bottle = items.bottle(self.connection)
		bottle.writeToDB()
		itemPouch = inventory.Inventory(self.connection)
		itemPouch.addItem(bottle.subType.value, 3)
		itemPouch.writeToDB()
		print(itemPouch, itemPouch.code)
		self.buckPasser.addInventory(itemPouch)
		self.__save()
		#os.system('reset')

	def __load(self, dbFile):
		pass

	def __save(self):
		self.connection.commit()
		self.currRoom = 0

	def __getObject(self, objName = None):
		if self.currRoom.objects == None:
			print("There's nothing in here")
			return
		try:
			self.inspection = [obj for obj in self.currRoom.objects if obj.objName.value.lower() == objName][0]
			return True
		except IndexError:
			raise UserWarning('No Object Found')

	def __getCharacter(self, charName = None):
		if self.currRoom.characters == None:
			print('You\'re all alone')
			return
		try:
			self.inspection = [character for character in self.currRoom.characters if character.charName.value.lower() == charName][0]
			return True
		except IndexError:
			raise UserWarning('No Character Found')

	def __getRoom(self, roomName = None):
		try:
			roomCode = Room.roomDict[roomName]
			self.inspection = Rooms.roomFactory(self.connection, roomCode)
		except KeyError:
			raise UserWarning('No Room Found')

	def __getItem(self, itemName = None):
		if self.buckPasser.inventory == None or self.buckPasser.inventory.items ==  None or len(self.buckPasser.inventory.items) < 1:
			print('You ain\'t got shit')
			return
		try:
			self.inspection = [item for item in self.buckPasser.inventory.items if item.item.subType.value.lower() == itemName][0]
			return True
		except IndexError:
			raise UserWarning('No Item Found')

	def __runCommand(self, command = None, args = None):
		try:
			if(args == None):
				func = self.inspection.__dict__['commands'][command].run()
			else:
				func = self.inspection.__dict__['commands'][command].run(args)
		except KeyError:
			pass

	def __makeCommand(self, subject = None, command = None, args = None, onObject = False, onCharacter = False, onItem = False):
		if type(subject) in [list, set, tuple]:
			subject = ' '.join(subject).lower().strip()
		try:
			#set the type of items its supposed to search for
			if onObject:
				try:
					self.__getObject(subject)
					self.__runCommand(command = command, args = args)
				except UserWarning:
					pass
			if onCharacter:
				try:
					self.__getCharacter(subject)
					self.__runCommand(command = command, args = args)
				except UserWarning:
					pass
			if onItem:
				try:
					self.__getItem(subject)
					self.__runCommand(command = command, args = args)
				except UserWarning:
					pass
		except UserWarning as uw:
			print(uw)
			print("I don't know what you're jabbering about you driveling idiot")

	def __exit(self):
		self.__save()
		exit(0)

	def mute(self):
		try:
			self.musicProcess.terminate()
		except:
			pass

	def music(self, args = None):
		musicDir = 'music'
		if args != None:
			if('mute' in args):
				mode = 'mute'
			elif('shuffle' in args):
				mode = 'shuffle'
			elif('single' in args or 'song' in args):
				mode = 'single'
			elif('playlist' in args):
				mode = 'playlist'
			else:
				return
		else:
			options = (('Single Song', 'single'), ('Playlist', 'playlist'), ('Shuffle All', 'shuffle'), ('Turn Off', 'mute'))
			mode = options[toolBag.printSelect(options = [option[0] for option in options], cursor = 'music> ')][1]

		self.mute()
		if(mode != 'mute'):
			self.musicProcess = toolBag.music(musicDir, mode = mode)

	def printCommands(self):
		print("Some of the Avaliable Commands:")

		maxLen = int(max(numpy.array([len(command) for command in self.commands if not self.commands[command].hide])))
		for command in self.commands:
			if not self.commands[command].hide:
				print('{0}{1} -> {2.descrip}'.format(' '*(maxLen - len(command)), command, self.commands[command]))

	def printHelp(self):
		print('\n\nNo one can help your sorry ass, just go score some blow.\n\n')
		self.printCommands()

	def use(self, subject = None):
		if subject == None:
			subject = [input('Use What? :  ').strip().lower()]
		self.__makeCommand(subject = subject, command = 'use', onObject = True, onItem = True)

	def describe(self, subject):
		if subject == None:
			subject = [input('Describe What? :  ').strip().lower()]
		self.__makeCommand(subject = subject, command = 'describe', onObject = True, onCharacter = True, onItem = True)

	def talkTo(self, charName = None):
		if self.currRoom.characters == None:
			print("No one is here")
			return
		if charName == None:
			charName = [input("Who do you want to talk to? ")]
		self.__makeCommand(subject = charName, command = 'talk', onCharacter = True)

	def grab(self, subject):
		if subject == None:
			subject = [input('Grab What? :  ').strip().lower()]
		self.__makeCommand(subject = subject, command = 'grab', onItem = True)

	def search(self, subject):
		if subject == None:
			subject = [input("Search what?")]
		self.__makeCommand(subject = subject, command = 'search', onCharacter = True)

	def listItems(self):
		self.buckPasser.listItems()

	def drop(self,subject):
		if subject == None:
			subject = [input("Drop what?")]
		self.__makeCommand(subject = subject, command = 'drop', args = self.currRoom, onItem = True)

	def move(self, room = None):
		'''
		change current room to an available neighbor.
		if the room code is a valid room, change the currRoom object to the corresponding room and print the room description
		'''
		if room == None:
			room = [input('To Where?> ').strip().lower()]
		self.__getRoom(room[0])

		if str(self.inspection.code) in self.currRoom.neighbors.value.split(','):
			os.system('clear')
			self.currRoom = self.inspection
			self.currRoom.look()
		else:
			raise UserWarning("{} is not a valid neighbor".format(room[0]))

	def run(self):
		os.stderr = open('log.log', 'w+')
		self.connection = sqlite3.connect(self.dbFile)
		try:
			self.__setupGame()
			self.currRoom = Rooms.HomeApt(self.connection)
			self.currRoom.loadRoom()
			self.currRoom.look()

			lastRoom = self.currRoom
			investDict = self.commands
			#investDict.update()

			while True:
				try:
					if lastRoom != self.currRoom:
						lastRoom = self.currRoom
						investDict = self.commands
						investDict.update(self.currRoom.commands)

					userInput.userInput(investDict, input('  > '))

				except:
					print(traceback.format_exc())
					exit(0)
			self.__save()
		finally:
			self.connection.close()
os.system('rm *.db')
Game().run()
