#inventory.py
from sqlTable import SQLTable, StagedSqlTable
import items
from menus import *
import userInput

'''
inventory commands:
	-> put bottle 3
	-> take bottle 3 or take 3 bottles
	-> drop 3 bottles
	-> combine bottle, rag, gasoline -> replace these with moltov
'''

class InventoryEntry(object):
	def __init__(self, db):
		self.db = db
		self.amount = None
		self.item = None

	def loadEntry(self, itemCode, amount):
		self.amount = amount
		self.item = items.Item(self.db)
		self.item.code = itemCode
		self.item.readFromDB()

class Inventory(SQLTable):#when interfacing w/ the db need to loop through all the items and their count as its duplicated
	'''
	Inventory is the base class for the hero, passive, and character classes
	'''
	def __init__(self, db):
		SQLTable.__init__(self, db)
		self.table = 'inventory'
		self.codeName = 'inventoryCode'
		self.amount = self.elementTable.addElement(title = 'Item Amount', name = 'amount', value = None, elementType = 'FLOAT')
		self.itemCode = self.elementTable.addElement(title = 'Item Code', name = 'itemCode', value = None, elementType = 'INT')
		self.items = None

		self.assignCode()

	def addAmount(self, itemCode, amount):
		'''
		If the item already is in the items, combine amounts
		'''
		for inventEntry in self.items:
			if int(inventEntry.item.code) == int(itemCode):
				inventEntry.amount += float(amount)
				self.amount.value = inventEntry.amount
				self.itemCode.value = inventEntry.item.code
				break#update amount in db and exit

	def addNewItem(self, itemCode, amount):
		'''
		No entry of this item exists, so add it
		'''
		newEntry = InventoryEntry(self.db)
		newEntry.loadEntry(itemCode, float(amount))
		self.items.append(newEntry)
		self.amount.value = newEntry.amount
		self.itemCode.value = itemCode

	def addItem(self, itemCode, amount):
		'''
		Loads in an inventory entry and writes change to database
		'''
		if self.items is None:
			self.items = []

		if self.itemInInventory(itemCode):
			self.addAmount(itemCode, amount)
			self.updateTable()
		else:
			#this item doesn't exist in this inventory, add the item and write it to the database
			self.addNewItem(itemCode, amount)
			self.writeToDB()

	def loadItem(self, itemCode, amount):
		'''
		Loads in an inventory entry but does not write to database
		'''
		if self.items is None:
			self.items = []

		if self.itemInInventory(itemCode):
			self.addAmount(itemCode, amount)
		else:
			#this item doesn't exist in this inventory, add the item and write it to the database
			self.addNewItem(itemCode, amount)

	def getItemEntryByName(self, itemName):
		for inventEntry in self.items:
			if inventEntry.item.itemName.value == itemName:
				return inventEntry
		return None #item not in inventory

	def getItemEntry(self, itemCode):
		for inventEntry in self.items:
			if inventEntry.item.code == itemCode:
				return inventEntry
		return None #item not in inventory

	def _moveItem(self, itemName, amount):
		inventEntry = self.getItemEntryByName(itemName)
		if inventEntry is None:
			raise UserWarning("Item {} doesn't exist".format(itemName))

		if(float(amount) <= 0):
			raise UserWarning("You can't move an amount <= 0 you clot")

		if(float(amount) > float(inventEntry.amount)):
			raise UserWarning("You don't have enough to do that")
		remaining = float(inventEntry.amount) - float(amount)

		if remaining < 1e-3:#FIXME this is gross
			self.items.pop(self.items.index(inventEntry))
			self.deleteSql(inventEntry.item.tableCode)#delete item from inventory
		else:
			inventEntry.amount = remaining
		return (inventEntry.item.code, amount)

	def placeItem(self, inventory, itemName, amount):
		'''
		moves an item from this inventory to that of another inventory
		'''

		assert(isinstance(inventory, Inventory))
		try:
			itemCode, itemAmount = self._moveItem(itemName, amount)
			assert(itemAmount == amount)
			inventory.addItem(itemCode, itemAmount)
		except UserWarning as uw:
			print(uw)

	def readFromDB(self):
		resp = self.selectSql(columnNames = self.columnNames, conditions = (self.tableCode))
		if(resp is None):
			raise UserWarning("No inventory for this code '%s'"%(self.code))
		self.items = None
		for amount, itemCode in resp:
			self.loadItem(itemCode, amount)

	def itemInInventory(self, itemCode):
		try:
			itemCode = int(itemCode)
		except (ValueError, TypeError):
			raise UserWarning("Item code {} is not a number".format(itemCode))

		if self.checkEntryLength() == 0:
			return False
		else:
			for entry in self.items:
				if itemCode == int(entry.item.code):
					return True
			return False

	def itemInInventoryByName(self, itemName):
		if self.checkEntryLength() == 0:
			return False
		else:
			for entry in self.items:
				if itemName == (entry.item.itemName.value):
					return True
			return False

	def checkEntryLength(self):
		if type(self.items) not in [list, tuple]:
			return 0
		else:
			return len(self.items)

	def checkItemAmount(self, itemCode):
		entry = self.getItemEntry(itemCode)
		if int(itemCode) == entry.item.itemCode:
			return float(entry.amount)

	def refreshList(self):
		if not self.checkEntryLength():
			return
		self.menu.listItems = []
		self.menu.addListItem(['Name', 'Amount', 'Total Weight'])
		for inventEntry in self.items:
			weight = float(inventEntry.item.weight.value) * float(inventEntry.amount)
			self.menu.addListItem([inventEntry.item.itemName.value, inventEntry.amount, "%.3f"%weight])

	def parseTransaction(self, inventory, args):
		'''
		Takes an inventory and an aray of args. Tests to see if either the first or 2nd arg is a known item, if it is the other (first or 2nd) is taken as the amount to be passed to put or take, returns the item name and amount. Otherwise raises a user warning.
		'''
		amount = None
		if(inventory.itemInInventoryByName(args[0])):
			itemName = args[0]
			if len(args) >= 2:
				amount = args[1]

		elif(inventory.itemInInventoryByName(args[1])):
			itemName = args[1]
			if len(args) >= 2:
				amount = args[0]

		else:
			raise UserWarning("Unknown arguments {}".format(args))

		try:
			float(amount)
		except (ValueError, TypeError):
			amount = None

		if amount is None:
			try:
				amount = float(input('Amount?> '))
			except ValueError:
				userInput.printToScreen("What?")
		return(itemName, amount)

class CharacterInventory(Inventory):
	def __init__(self, db):
		Inventory.__init__(self, db)

class PassiveInventory(Inventory):
	'''
	Inventory for rooms and objects
	'''
	def __init__(self, db, title = None, charInventory = None):
		Inventory.__init__(self, db)

		self.menu = ListMenu(db = db, title = title, description = "Inventory", cursor = "Inventory> ", closeOnPrint = True, fields = 3, fieldLengths = [.3,.3,.4])
		self.menuCommands = {
		'put':userInput.Command(func=self.put, takesArgs=True, descrip = 'Move an item to this inventory'),
		'take':userInput.Command(func=self.take, takesArgs=True, descrip = 'Take an item')
		}
		self.menu.commands.update(self.menuCommands)

		self.charInventory = charInventory

	def put(self, args):
		'''
		Add an item to this inventory from charInventory
		'''
		try:
			itemName, amount = self.parseTransaction(self.charInventory, args)
		except UserWarning:
			userInput.printToScreen("Item doesn't exist")
			return

		try:
			self.charInventory.placeItem(itemName, amount)
			self.refreshList()
		except UserWarning:
			userInput.printToScreen("Item doesn't exist or insufficient quantities for transaction")

	def take(self, args):
		'''
		move an item from this inventory to the charInventory
		'''

		itemName, amount = self.parseTransaction(self, args)
		try:
			self.placeItem(self.charInventory, itemName, amount)
			self.refreshList()
		except UserWarning:
			userInput.printToScreen("Item doesn't exist or insufficient quantities for transaction")

	def runMenu(self):
		self.refreshList()
		self.menu.runMenu()

class HeroInventory(Inventory):
	'''
	The players inventory, allows dropping items to the current room, and combining items
	'''
	def __init__(self, db, roomInventory = None):
		Inventory.__init__(self, db)
		title = "Inventory"

		self.menu = ListMenu(db = db, title = title, description = "Inventory", cursor = "Inventory> ", closeOnPrint = True, fields = 3, fieldLengths = [.3,.3,.4])
		self.menuCommands = {
		'drop':userInput.Command(func=self.drop, takesArgs=True, descrip = 'Drop an item on the floor')
		}
		self.menu.commands.update(self.menuCommands)

		self.roomInventory = roomInventory

	def drop(self, args):
		try:
			itemName, amount = self.parseTransaction(self, args)
		except UserWarning:
			userInput.printToScreen("Item doesn't exist {}".format(args))
			return

		try:
			self.placeItem(self.roomInventory, itemName, amount)
			self.refreshList()
		except UserWarning:
			userInput.printToScreen("Item doesn't exist or insufficient quantities for transaction")

