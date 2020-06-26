import unicodedata
from PyQt5.QtCore import QThread
from PyQt5 import uic, Qt, QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from datetime import datetime
import sys
import json
import os
import csv
import forwader
import globalVariables as variables
import connectionThread
import shutil

class driver(Qt.QWidget): #The Application's UI is built using QT framework and the class is of type QWidget, a C written library, for documentation refer to https://doc.qt.io/qtforpython/
    def __init__(self): #class init 
        super(driver, self).__init__()
        uic.loadUi('ui/main.ui', self) #loading the external main.ui file into self from ui/main.ui (this class will now hold all the widgets added in main.ui)
        self.show() # show() is a method used to show the window   
        self.setWindowTitle("Whatsapp Forwader") # setting the title displayed on the window
        self.imgPath = "" # This variable will hold the image path, if no image is chosen, it will remain empty
        self.Message = "" # This variable will hold the message to be forwarded, it can be empty only if the image path is not empty (for messages only containing images)
        self.Forwards = "" # This will hold the number of forwards desired
        self.errorWindow = errorWindow() # initializing the error window to show in case there are any input errors
        self.connErr = errorWindow() # initializing the error window to show in case thr internet connection timed out 
        self.loadedJsonFile = None # this will hold the Json File of a loaded reccord (the type of the variable will be File writer)
        self.loadedCsvFile = None # this will hold the Csv File of a loaded reccord (the type of the variable will be File writer)
        self.importedNamesCsvFile = None # if the user specifies a traget audience which should receive the message, this is the csv file that's in charge of that
        self.contactDict = {} # This is s hash map that will hold all the contact Names (for this type of project a hash map is the most efficient data type to use since if has a O(1) complexity when searching if the contact was already scanned)
        self.importedContactDict = {} # same as above, but this will hold the entire contact Names of the imported csv file for target clients (remains empty if there is no imported file)
        self.remainingContactDict = {} # This will hold the remaining contact Names to scan if the record was chosen and that record had target clients
        self.WhatsappForwader = forwader.WhatsappForwader() # initializing the forwader class
        self.connectionThread = connectionThread.connectionThread() # initializing the connection class
        self.connectionThread.connectionInterruptSignal.connect(self.checkConnection) # linking the method checkConnection() from this class to a signal from the connection Thread
        self.WhatsappForwader.strContactSignal.connect(self.appendName) # linking the method appendName() from this class to the forwader class
        self.WhatsappForwader.updatePBsignal.connect(self.updatePB) # linkning method
        self.loadRecordBtn.clicked.connect(self.load_record) # linking method
        self.startBtn.clicked.connect(self.runThread) # linking method
        self.imageBtn.clicked.connect(self.chooseImg) # linking method
        self.importNamesBtn.clicked.connect(self.importNames) # linking method
        self.recordList.currentRowChanged.connect(self.enableLoadBtn) # linking method
        self.searchTxt.textChanged.connect(self.searchContacts) # linking method
        if (not os.path.isdir('records')): # first time the program runs it will create a records directory which will hold a list of previously sent message with all of its data
            os.mkdir('records')
        self.setUpViews()
        self.WhatsappForwader.loadWebsite() # this function from the forwader loads the www.web.whatsapp.com website
        self.connectionThread.start() # start the connection listener thread

    def setUpViews(self): # --------UI STUFF---------
        baseStyleSheet = "background-color: #cbcbcb; color : black;" # setting style sheets (these are like css, they set UI properties for our widgets)
        btnStyleSheet = "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;" # setting style sheets (these are like css, they set UI properties for our widgets)
        widgetsStyleSheet = "background-color : white; border: 1px solid #139e2d"# setting style sheets (these are like css, they set UI properties for our widgets)
        self.progressBar.setVisible(False) # at start the progress bar is invisible because we dont know how many forwards we have
        self.progressLbl.setVisible(False) # this is the label of the progress bar the one showing d/d
        self.loadRecordBtn.setEnabled(False) # we enable the button which lets us load a previously stored record
        self.loadRecordBtn.setStyleSheet( 
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;") # setting style sheet
        self.setStyleSheet(baseStyleSheet) # setting style sheet
        self.imageLbl.setScaledContents(True) # this method scales the image (if any) to fit the label widget in the ui, this does not affect the original image in any way
        self.imageLbl.setStyleSheet(widgetsStyleSheet)  # setting style sheet
        self.recordList.setStyleSheet(widgetsStyleSheet) # setting style sheet
        self.contactList.setStyleSheet(widgetsStyleSheet) # setting style sheet
        self.searchTxt.setStyleSheet(widgetsStyleSheet) # setting style sheet
        self.forwardsTxt.setStyleSheet(widgetsStyleSheet) # setting style sheet
        self.messageTxt.setStyleSheet(widgetsStyleSheet) # setting style sheet
        self.imageBtn.setStyleSheet(btnStyleSheet) # setting style sheet
        self.importNamesBtn.setStyleSheet(btnStyleSheet) # setting style sheet
        self.startBtn.setStyleSheet(btnStyleSheet) # setting style sheet
        self.getFiles() # adds file names from "records/" directory if they exist
        self.show() # refresh attached widgets

    def runThread(self): # start the forwader thread (once the start button is clicked from the window this function will execute)
        self.Message = self.messageTxt.toPlainText() # fetching the message form the UI
        self.Forwards = self.forwardsTxt.toPlainText() # fetching thenumber of forwards form theUI

        if self.Message == "" and self.imgPath == "": # if Message and Image path are both not definad show the error window
            self.errorWindow.setErrorMsg(
                "Please fill in at least one of the two :\n-Image path\n-Text Message\nOtherwise the program will not run")
            self.errorWindow.show()

        elif self.Forwards == "": # if the Number of forwards is not definad show the error window
            self.errorWindow.setErrorMsg(
                "Please set the number of forwards")
            self.errorWindow.show()

        elif (not self.is_number(self.Forwards)) or int(self.Forwards) < 1: # if the forward number is not valid as a number, show the error window
            self.errorWindow.setErrorMsg(
                "Please enter a valid number of forwards")
            self.errorWindow.show()

        elif (self.loadedCsvFile != None and self.loadedJsonFile != None and self.importedNamesCsvFile == None): # this is the case where you are startin completely new Forward WITHOUT target clients
            self.WhatsappForwader.setForwards(self.Forwards) # Setting the number of forwards to the forwader
            self.WhatsappForwader.setImagePath(self.imgPath) # Setting the image path to our forwader
            self.WhatsappForwader.setMessage(self.Message) # Setting the Message to our forwader
            self.WhatsappForwader.setFileName(self.loadedFileName) # if there is a loaded record we send it to our forwader here
            self.WhatsappForwader.setContactMode(variables.NEW_NAMES) # setContactMode is function that defines whether we are using targeted clients or we're starting fresh
            self.MODE = variables.NEW_NAMES # setting the contact mode in this class aswell
            self.WhatsappForwader.setContactDict(self.contactDict) # here we are passing the contacts names to our forwader 
            self.WhatsappForwader.setPreviewMode( 
                self.previewCheckBox.isChecked()) # if the preview mode checkbox in the window is checked, self.previewCheckBox.isChecked() will return true otherwise returns false 
            self.WhatsappForwader.setIsDelayMode(self.delayCheckBox.isChecked()) # same as above for the delay checkbox (used to set delay betweeen messages (30 to 60 seconds))
            self.WhatsappForwader.start() # start the forwader thread
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")  # setting style sheet

        elif (self.loadedCsvFile == None and self.loadedJsonFile == None and self.importedNamesCsvFile != None):  # this is the case where you are starting a completely new Forward WITH target clients
            currentDate = datetime.today().strftime("%Y-%m-%d %H-%M-%S") # we create a name for the folder which will hold all the data of this sessio,  the name of the folder is the current time in the format of YY-mm-dd hh:mm:ss
            os.makedirs(f'records/{currentDate}') # os.makedirs creates teh folder with teh given name
            jsonFile = open(f'records/{currentDate}/record.json', 'w+') # here we create a new file record.json in the created folder 
            if self.importedNamesCsvFile != None:
                open(f'records/{currentDate}/importedNames.csv', 'w+') # open the imported names file if there is any 
                shutil.copy2(self.importedNamesCsvFile.name, f'records/{currentDate}/importedNames.csv') # make a copy of the imported names csv file and save it on the local folder 
            jsonData = {
                "date": currentDate,
                "Forwards": self.Forwards,
                "Message": self.Message,
                "imagePath": self.imgPath,
                "importedNames": 'False' if self.importedNamesCsvFile == None else 'True'
            } # this is the structure of the data that will be saved in json file 
            json.dump(jsonData, jsonFile) # dumping the data into the json file
            self.progressBar.setVisible(True) # setting the prograss bar to be visisble since we now know the number of forwards 
            self.progressLbl.setVisible(True) # setting the label of the progress bar visible for the same reason mentioned above
            self.WhatsappForwader.setContactMode(variables.IMPORTED_NAMES) # We tell the forwader that the contacts are imported 
            self.MODE = variables.IMPORTED_NAMES # we notify this class that we are working with imported names 
            self.progressLbl.setText(f"0/{self.Forwards}") # we set the text of the progress bar 
            self.progressBar.setMaximum(int(self.Forwards)) # setting the maximum value for the progress bar (aka the number of forwards desired)
            self.progressBar.setMinimum(0) # min is always 0 ...
            self.progressBar.setValue(len(self.importedContactDict)) # if we have record that had imported names and was loaded, the progress bar will automatically set the value of the number of contacts that were already scanned 
            self.WhatsappForwader.setForwards(self.Forwards) # set the number of forwards for the forwader 
            self.WhatsappForwader.setImagePath(self.imgPath) # set the image path if any for the forwader
            self.WhatsappForwader.setContactDict(self.importedContactDict) # we send the loaded contact hashmap for the forwader 
            self.WhatsappForwader.setMessage(self.Message) # sending message for the forwader
            self.WhatsappForwader.setFileName(currentDate) # sending the folder name for the forwader (it needs it because it writes directly to the files inside the folder to update the scanned names)
            self.WhatsappForwader.loadCsvFile() # this is the csv file contained in the above mentioned folder , i'm just opening it to get things ready and start adding scanned contact names to it 
            self.WhatsappForwader.setPreviewMode(
                self.previewCheckBox.isChecked()) # setting if preview mode from checkbox
            self.WhatsappForwader.setIsDelayMode(self.delayCheckBox.isChecked()) # setting if with delay from checkbox
            self.WhatsappForwader.start() # start the thread 
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;") # setting style sheet

        elif (self.loadedCsvFile != None and self.loadedJsonFile != None and self.importedNamesCsvFile != None):  # this is the case where you are continuing a previous forward specified from a record file WITHOUT target clients
            self.WhatsappForwader.setForwards(self.Forwards) # refer to above documentation to see what each function of the forwader does
            self.WhatsappForwader.setImagePath(self.imgPath)
            self.WhatsappForwader.setMessage(self.Message)
            self.WhatsappForwader.setFileName(self.loadedFileName)
            self.WhatsappForwader.setContactMode(variables.IMPORTED_NAMES)
            self.MODE = variables.IMPORTED_NAMES
            self.WhatsappForwader.setContactDict(self.remainingContactDict)
            self.WhatsappForwader.setPreviewMode(
                self.previewCheckBox.isChecked())
            self.WhatsappForwader.start()
            self.WhatsappForwader.setIsDelayMode(self.delayCheckBox.isChecked())
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;") # setting style sheet

        else: # this is the case where you are continuing a previous forward specified from a record file WITH target clients
            currentDate = datetime.today().strftime("%Y-%m-%d %H-%M-%S") # refer to above documentation to see what each function of the forwader does
            os.makedirs(f'records/{currentDate}')
            jsonFile = open(f'records/{currentDate}/record.json', 'w+')
            jsonData = {
                "date": currentDate,
                "Forwards": self.Forwards,
                "Message": self.Message,
                "imagePath": self.imgPath,
                "importedNames": 'False' if self.importedNamesCsvFile == None else 'True'
            }
            json.dump(jsonData, jsonFile)
            self.progressBar.setVisible(True)
            self.progressLbl.setVisible(True)
            self.WhatsappForwader.setContactMode(variables.NEW_NAMES)
            self.MODE = variables.NEW_NAMES
            self.progressLbl.setText(f"0/{self.Forwards}")
            self.progressBar.setMaximum(int(self.Forwards))
            self.progressBar.setMinimum(0)
            self.progressBar.setValue(len(self.contactDict))
            self.WhatsappForwader.setForwards(self.Forwards)
            self.WhatsappForwader.setImagePath(self.imgPath)
            self.WhatsappForwader.setMessage(self.Message)
            self.WhatsappForwader.setFileName(currentDate)
            self.WhatsappForwader.loadCsvFile()
            self.WhatsappForwader.setPreviewMode(
                self.previewCheckBox.isChecked())
            self.WhatsappForwader.setIsDelayMode(self.delayCheckBox.isChecked())
            self.WhatsappForwader.start()
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;") # setting style sheet

    def load_record(self): # when the user clicks on load record button this function will execute 
        if self.importedNamesCsvFile == None : # if we don't have imported names
            if self.loadedCsvFile == None: # if there is a loaded csv file that means a record is already loaded, and the button will serve to unload the record, refer to the "else" linked to this "if" to see how i'm unloading the file   
                if (self.recordList.currentItem()): # now that we're here, it means we are 100% loading a record 
                    self.loadRecordBtn.setText("unload") # the load button switches to unload because there's a record from the list that is being loaded 
                    self.loadedFileName = str(self.recordList.currentItem().text()) # here we get the name of the folder holding the entire data of the selected record (i'm getting the name of the file as plain text from the list widget containing the names of all the folder records)
                    self.loadedJsonFile = open(
                        f'records/{self.loadedFileName}/record.json', 'r') # opening and loading the json file containing all the data from the record
                    self.loadedCsvFile = open(
                        f'records/{self.loadedFileName}/record.csv', 'r') # opening and loading the csv file containing the scanned names
                    data = json.load(self.loadedJsonFile) # fetching the raw json from the above json file, "data" now holds all the parameters used in the record
                    self.messageTxt.setText(data["Message"]) # data ['Message'] returns the content of Message form the json
                    self.forwardsTxt.setText(data["Forwards"]) # data ['Forwards'] returns the number of forwards from the json
                    self.imgPath = data["imagePath"] # data ['imagePath'] returns the image path if any from the json, if there was no image in the record the default value is ""

                    if data["importedNames"] == "True" : # if the record has imported names fetch the file containing those names from the record folder
                        self.importedNamesCsvFile = open(
                            f'records/{self.loadedFileName}/importedNames.csv', 'r') # opening the folder in 'r' mode aka read only mode 
                        self.forwardsTxt.setText(data["Forwards"]) 

                    if self.imgPath != "": # if there is an image in the record load it 
                        self.imageLbl.setPixmap(Qt.QPixmap(self.imgPath)) # loading the image in the image label from the UI
                    self.disableInputs() # this function disables all the inputs in the window that are filled by the record, the user CANNOT change any data that came from the loaded record from the windo, IF you REALLY need to change the record's contents go to package contents of the Application and modify the record's data manually, DO THIS AT YOUR OWN RISK
                    self.populateContactList() # all the contacts that were aready scanned (since we got them from the csv file) will be added to the list widget on the UI
                    forwards = int(data["Forwards"]) # getting the number of forwards from the json file 
                    self.Forwards = forwards
                    self.progressBar.setMaximum(forwards)
                    self.progressBar.setMinimum(0)
                    self.progressBar.setValue(len(self.contactDict))
                    self.progressLbl.setText(f"{len(self.contactDict)}/{forwards}")
                    self.progressBar.setVisible(True)
                    self.progressLbl.setVisible(True)

            else: # if we enter this else it means a file was alreay loaded and we want to unload it 
                self.enableInputs() # re-enable the inputs that were previously disabled
                self.loadRecordBtn.setText("load") # reset the button name to load if user wants to load a different file 
        else: # same as the above else
            self.enableInputs() 
            self.loadRecordBtn.setText("load")
        

    def disableInputs(self): # disable all the inputs that were filled by the loaded record 
        btnDisabledStyleSheet = "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;"
        self.forwardsTxt.setEnabled(False)
        self.messageTxt.setEnabled(False)
        self.imageBtn.setStyleSheet(btnDisabledStyleSheet) # setting style sheet
        self.imageBtn.setEnabled(False)
        self.importNamesBtn.setStyleSheet(btnDisabledStyleSheet)
        self.importNamesBtn.setEnabled(False)
        self.progressBar.setVisible(True)
        self.progressLbl.setVisible(True)

    @QtCore.pyqtSlot(bool, name="boolSignal") # this function receives a boolean 
    def checkConnection (self, connected): # this is a function that is linked to the connection thread, will receive a result every 2 seconds from seconds eith a boolean, if bool is False it means there is no internet and we need to stop the program, otherwise continue normally
        if (not connected): # if the bool received is false go here
            self.connErr.setErrorMsg(
                    "You appear to be offline, once you're connected to the internet the program will resume automatically")
            self.connErr.show() # show the internet error message
            self.connErr.okBtn.setVisible(False) 
            self.startBtn.setEnabled(False) # User MUST wait until internet comes back (aka when this function receives a TRUE bool) and can't do anything
            self.startBtn.setStyleSheet("background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;") # setting style sheet
            self.WhatsappForwader.state = False # stopping the forwader 
            
        else : # here we recive a TRUE bool (aka there is internet)
            self.connErr.close() # if there was an error window shown, close it  
            self.connErr.okBtn.setVisible(True)
            if not self.WhatsappForwader.isRunning() : # if there was no internet resume the forwader 
                self.startBtn.setEnabled(True)
                self.startBtn.setStyleSheet(
                "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;") # setting style sheet
            self.WhatsappForwader.state = True





    def enableLoadBtn(self): # enable the load button in the UI 
        self.loadRecordBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;") # setting style sheet
        self.loadRecordBtn.setEnabled(True)
        self.forwardsTxt.setEnabled(True)
        self.forwardsTxt.setText("")


    def disableLoadBtn(self): # disable the load button in the UI 
        self.loadRecordBtn.setEnabled(False)
        self.forwardsTxt.setEnabled(False)
        self.loadRecordBtn.setStyleSheet("background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;") # setting style sheet

    def importNames(self): # import targeted contact names (csv file)
        if (self.importedNamesCsvFile == None): # if there is no already defined imported contacts file 
            filepicker = filePicker() # start a file picker
            filePath= filepicker.getFilePath() # get the path of the chosen file 
            if filePath != "": # if there was a file chosen
                self.importedNamesCsvFile = open( 
                        filePath, 'r') # open the file and load it 
                self.populateContactList() # populate the list widget with the contact names 
                self.disableLoadBtn() # you CANNOT load a record when you already defined a file for targeted contact names, because the record has it's own csv file with contact names
                self.forwardsTxt.setText(str(len(self.importedContactDict))) # automatically setting the number of forwards which iss the number of imported client names
                self.importNamesBtn.setText("Unload") # changing the import button to unload 
        else : # here we unload the imported names 
            self.importedContactDict = {}
            self.importedNamesCsvFile = None
            self.contactList.clear()
            self.importNamesBtn.setText("Targeted Clients")
            self.enableLoadBtn()

    def searchContacts(self): # this function triggers every time the search input is changes by a character 
        # We search for anything that matches the search input in our List of
        # Contact names
        searchValue = self.searchTxt.toPlainText() # getting the search input as plain text
        matchedNames = self.contactList.findItems(
            searchValue, QtCore.Qt.MatchContains) # we get the list of matched names from the list, QtCore.Qt.MatchContains is a regex that will return contact names is a *name* format
        listItems = [self.contactList.item(i)
                     for i in range(self.contactList.count())] # loading all the list widget Items in the local variable listItem
        for name in listItems: # iterating through every element in the list widget (aka every contact name)
            if name not in matchedNames: # if the name did not match the search query (aka is not in the list of matched elements)
                name.setHidden(True) # hide the element from the list
            else:
                name.setHidden(False) # otherwise show it

    def populateContactList(self): # populate the list widgets in our UI 
        if self.importedNamesCsvFile == None and self.loadedCsvFile != None : # this case we are adding contact names from a loaded Csv file from a record 
            reader = csv.DictReader(self.loadedCsvFile) # we create a reader that will scan the Csv file 
            for row in reader: # for every row in our Csv file 
                self.contactDict[row['Name']] = 1 # we load the contact name into our hashmap so it doesn't scan it again 
                item = QtWidgets.QListWidgetItem(row['Name']) # add the name to the list widget in the UI 
                self.contactList.addItem(item) # add the list element to the list widget 

        elif self.importedNamesCsvFile != None and self.loadedCsvFile == None : # this is the case where we have an imported contact name file 
            reader = csv.DictReader(self.importedNamesCsvFile) # we create a reader that will scan the Csv file 
            for row in reader:# for every row in our Csv file 
                self.importedContactDict[row['Name']] = 1 # we load the contact name into our hashmap so it doesn't scan it again 
                item = QtWidgets.QListWidgetItem(row['Name']) # add the name to the list widget in the UI 
                color = Qt.QColor() # creating a color attribute for the list widget item
                color.setRgb(236,192,192) # setting the color to lite red because the contact name hasn't been scanned yet 
                item.setBackground(color) # applying the color to the list widget item 
                self.contactList.addItem(item) # adding the list widget item to the list widget 
            
        elif self.importedNamesCsvFile != None and self.loadedCsvFile != None : # this is the case where we have loaded record that had an imported contact names file 
            reader = csv.DictReader(self.importedNamesCsvFile) # we create a reader that will scan the imported contact names Csv file 
            readerScanned = csv.DictReader(self.loadedCsvFile) # we create a reader that will scan the already scanned contact names Csv file 
            for row in reader: # for every contact name in the imported csv file  
                self.importedContactDict[row['Name']] = 1 # add the name to this hashmap
            for row in readerScanned: # for every contact name in the csv file containing already scanned names 
                self.contactDict[row['Name']] = 1 # add the name to this hashmap
            
            for key in self.importedContactDict: # for every contact name in the imported hashmap
                if self.contactDict.get(key): # if the contact name is already scanned (aka already present in the contactDict hashmap)
                    item = QtWidgets.QListWidgetItem(key) # create a list widget item 
                    color = Qt.QColor() # create a color attribute
                    color.setRgb(195,236,192) # set the color to lite green, signifying that the contact has already received the message and was scanned 
                    item.setBackground(color) # set the color to the listwidget item 
                    self.contactList.addItem(item) # add the item to the list widget 
                else : # if the contact did not receive the message yet (aka not present in the contactDict hashmap)
                    item = QtWidgets.QListWidgetItem(key)  # create a list widget item 
                    color = Qt.QColor()# create a color attribute
                    color.setRgb(236,192,192)# set the color to lite red, signifying that the contact did not receive any message yet
                    self.remainingContactDict[key] = 1 # this is a hash map holding the remaining the contact names that should be scanned and will be passed to the forwader 
                    item.setBackground(color) # set the color to the listwidget item 
                    self.contactList.addItem(item) # add the item to the list widget 

    @QtCore.pyqtSlot(str, name="strSignal") # this function receives a string (contact name) form the forwader thread
    def appendName(self, name):  # name param is a contact name that was added
        if self.MODE == variables.NEW_NAMES: # if we're not woring with imported names 
            item = QtWidgets.QListWidgetItem(name) # add the contact name to the list widget 
            self.contactList.addItem(item)
        elif self.MODE == variables.IMPORTED_NAMES: # if we're woring with imported names 
            listElement = self.contactList.findItems(name, QtCore.Qt.MatchExactly) # the name that is received should be present in the list so here we fetch it
            if len(listElement) > 0: # since the name was received it means we just sent him the message (aka his color is still red)
                color = Qt.QColor() 
                color.setRgb(195,236,192)
                listElement[0].setBackground(color) # Change the element's color to light green signifying that he already received the message

    @QtCore.pyqtSlot(int, name="intSignal") # this function receives an integer (how many contacts the message was sent to in total) form the forwader thread
    def updatePB(self, val): 
        self.progressBar.setValue(val) # set the value of the progress bar 
        self.progressLbl.setText(f"{val}/{self.Forwards}") # update the label of the progress bar 

    def is_number(self, s): # just to check if the forwards input is a valid number 
        try:
            int(s)
            return True
        except ValueError:
            return False

    def enableInputs(self): # Enable inputs that were previously disabled from loading a record 
        btnActiveStyleSheet = "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;"
        self.forwardsTxt.setEnabled(True)
        self.forwardsTxt.setText("")
        self.contactDict = {}
        self.messageTxt.setEnabled(True)
        self.progressBar.setVisible(False)
        self.progressLbl.setVisible(False)
        self.progressBar.setValue(0)
        self.messageTxt.setText("")
        self.imageBtn.setStyleSheet(btnActiveStyleSheet) # setting style sheet
        self.imageBtn.setEnabled(True)
        self.importNamesBtn.setStyleSheet(btnActiveStyleSheet) # setting style sheet
        self.importNamesBtn.setEnabled(True)
        self.imageLbl.setPixmap(Qt.QPixmap(""))
        self.contactList.clear()
        self.imgPath = ""
        self.Forwards = ""
        self.Message = ""
        self.loadedCsvFile = None
        self.loadedJsonFile = None
        self.loadedFileName = None
        self.importedNamesCsvFile = None
        self.contactDict = {}
        self.importedContactDict = {}

    def getFiles(self): # here we get the list of record folders and add them to the list widget 
        records = os.listdir("records/") # get all the folders from the records directory
        for record in records: # looping over every folder
            if record != '.DS_Store': # ignore this ( this is just a cache file for the directory that is automatically added by the OS and is completely irrelevant )
                self.recordList.addItem(
                    QtWidgets.QListWidgetItem(
                        os.path.splitext(record)[0])) # Add the list widget element to the list widget 

    def chooseImg(self): # opening a file picker from where the user specifies the image path 
        filepicker = filePicker() # opening the file picker 
        self.imgPath = filepicker.getFilePath() # get the image path
        if self.imgPath != "": # if there was an image chosen 
            self.imageLbl.setPixmap(Qt.QPixmap(self.imgPath)) # setting the image as preview in the image label


class filePicker(Qt.QWidget): # this is the file picker class used to pick the imported names or the image path

    def __init__(self):
        super().__init__()
        self.title = 'Choose File'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.filePath = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.openFileNameDialog()
        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self, "QFileDialog.getOpenFileName()", "", "All Files (*)", options=options)
        if fileName:
            self.filePath = fileName

    def getFilePath(self):
        return self.filePath


class errorWindow(Qt.QWidget): # this is the error window class used to display runtime input errors or connection error
    def __init__(self):
        Qt.QWidget.__init__(self)
        uic.loadUi('ui/error.ui', self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.warningImg.setScaledContents(True)
        self.warningImg.setPixmap(Qt.QPixmap("ui/warning.png"))
        self.okBtn.clicked.connect(self.exitWindow)
        self.errorTxt.setWordWrap(True)

    def setErrorMsg(self, msg):
        self.errorTxt.setText(msg)

    def exitWindow(self):
        self.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = driver()
    app.exec_() # execute application 
