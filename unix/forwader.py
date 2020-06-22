from PyQt5.QtCore import QThread
from PyQt5 import uic, Qt, QtWidgets, QtCore
from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.common import exceptions
import unicodedata
import os
import random
import json
import csv
import selenium
import globalVariables as variables
from selenium.webdriver.common.keys import Keys

# -------------- Execution Steps --------------
# 1= Press on new chat button
# 2- Scan the contact list for new names
# 3- Click on the contact name 
# 4- Load the message or load the Image or Both 
# 5= Repeat All above steps until the requirements are reached 

class WhatsappForwader(QThread): # class init 

    strContactSignal = QtCore.pyqtSignal(str, name="strSignal") # a string signal that is linked to the driver function containing the name of the scanned contact (it adds it to the list widget in the main window)
    updatePBsignal = QtCore.pyqtSignal(int, name="intSignal") # an int signal notifying the total number of scanned contacts for the Progress Bar

    def __init__(self): # self init
        super(WhatsappForwader, self).__init__()
        self.state = True # this is the state of the forwader, if false the forwader will pause, if true the forwader will resume from where it stopped (this is mainly used for when internet times out)
        self.contactDict = {} # this is a hashmap that will hold the scanned contact names
        self.AllContacts = [] # this is a hash map that will hold the imported contact names (if a file was selected)
        self.isPreviewMode = True # this will hold the boolean received from the is preview mode checkbox in the window 
        self.withDelay = True # this will hold the boolean received from the is with delay checkbox in the window 
        self.MODE = 0 # this will define in which mode the forwader will run (either new names or imported names)

    def run(self):
        if(self.MODE == variables.NEW_NAMES): # if the mode is new names not imported names
            if (self.ImagePath == ""): # if there isn't any image specified
                time.sleep(1) # sleep for 1 second
                self.driver.find_elements_by_xpath (
                    '//div[@class=\'PVMjB\']')[1].click() # click on "new chat" button
                time.sleep(0.2) # sleep for 200 ms 
                elements = self.driver.find_elements_by_xpath(
                    '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]') # these are the contact elements (aka the contact names), if you analyse the html of the contact list you'll see that only about 20 
                    # contact elements are loaded (could be more depending on your screen size), even tho there are more than 20 contacts in the list, whatsapp only shows 20 for optimization reasons, when you scroll down the contact list, the 20 contact names that were visible 
                    # wll be overriden by new contact names and so on ... 
                scrollValue = 20 # this is the scroll value that will be executed in the scroll javascript command, i ran a lot of tests to find the optimal scroll value and this seems to be the best one
                currentScrollPos = 0 # when there are tons of contact names already scanned, the program will take a long time to scroll in the contact list to get to a new contact, so this variable will hold the scroll value of every new found contact name depending on the 
                # position of the contact name in the list, so when we press the new chat button after scanning a new name the program will automatically jump to where it found that name and start scanning new names from there

                while len(self.contactDict) < self.Forwards: # keep running until the number of contacts scanned reach the desired number of forwards  
                    
                    while self.state : # check if there is internet 

                        for element in elements: # for every contact in the list of the ~20 scanned contacts from the list 
 
                            if len(self.contactDict) == self.Forwards: # if we already reached the desired number of forwards break from the loop
                                self.state = False
                                break

                            try: # using try catch to handle exceptions 
                                innerSoup = BeautifulSoup( 
                                    element.get_attribute('innerHTML'), features="lxml") # get the element's (the contact) HTML content
                                rawContactName = innerSoup.div.div.get_text(strip=True) # here we get the raw contact name from the html element above
                                contactName = unicodedata.normalize( 
                                    "NFKD", rawContactName) # sometimes the HTML returns weird characters instead of whitespace, this takes care of it 
                                if (not self.contactDict.get(contactName) # if the contact name was not already scanned 
                                        and contactName != "New group"): 
                                    currentScrollPos = int(self.driver.execute_script(
                                        "return document.querySelector('div._1qDvT._2wPpw').scrollTop")) # svae the current position of the element in the contact list so that we resume from there next time we open the new chat list
                                    time.sleep(0.1) # sleep for 100 ms 
                                    message = self.formatMessage(
                                        self.Message, contactName) # this formats the message (check the formatMessage function for more info)
                                    print(
                                        "\nContact : "+contactName,
                                        "\nMessage : "+message)
                                    element.click() # click on the contact name 
                                    time.sleep(0.1) # sleep for 100 ms 
                                    try : # handeling thrown exceptions 
                                        self.driver.find_element_by_xpath(
                                            '//div[@class=\'_3uMse\']').send_keys(message) # this is the text input for the contact, we're simulating typing the message 
                                        time.sleep(0.1) # sleep for 100 ms 
                                        if self.withDelay : # if the delay checkbox was checked 
                                            time.sleep(random.randint(30,60)) # sleep for a random amount of time between 30 and 60 seconds 
                                        if not self.isPreviewMode: # if the preview mode checkbox is checked 
                                            self.driver.find_element_by_xpath( 
                                                '//button[@class=\'_1U1xa\']/span[1]').click() # click the send the message button
                                        self.contactDict[contactName] = 1 # add the contact name to the hashmap
                                        self.addContact([contactName]) # add the contact to the csv file 
                                        self.strContactSignal.emit(contactName) # send the contact name to add it to the list widget in the window 
                                        self.updatePBsignal.emit(len(self.contactDict)) # update the progress bar 
                                        time.sleep(0.1) # sleep for 100 ms 
                                    except exceptions.NoSuchElementException as e :
                                        self.contactDict[contactName] = 1 # contact was blocked and the input field was not found
                                        pass

                                    self.driver.find_elements_by_xpath(
                                        '//div[@class=\'PVMjB\']')[1].click() # click the "new chat" button to go back to the list of contacts 
                                    time.sleep(0.1) # sleep for 100 ms 
                                    self.driver.execute_script(
                                        f"document.querySelector('div._1qDvT._2wPpw').scrollTop += {currentScrollPos-200}") # scroll to where the last contact name was found (i deducted 200 just in case)
                                    time.sleep(0.1) # sleep for 100 ms 
                                    elements = self.driver.find_elements_by_xpath(
                                        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]') # override the elements (aka the 20 contact names) with new names since we're in a new scroll position, the contact names will update 

                                else: # if the contact was already scanned 
                                    self.driver.execute_script(
                                        f"document.querySelector('div._1qDvT._2wPpw').scrollTop += {scrollValue}") # scroll 20 px to get new names
                                    elements = self.driver.find_elements_by_xpath(
                                        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]') # override the elements to fetch updated names

                            except (exceptions.StaleElementReferenceException, exceptions.NoSuchElementException, exceptions.JavascriptException) as e: 
                                pass  # Same contact element was read, or contact was blocked and the input field was not found

            else: # if user specified an image 
                time.sleep(1) # sleep for 1 second
                self.driver.find_elements_by_xpath(
                    '//div[@class=\'PVMjB\']')[1].click() # click the new chat button
                time.sleep(0.2) # sleep for 200 ms 
                elements = self.driver.find_elements_by_xpath(
                    '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]') # get the elements from the contact list 
                scrollValue = 20 # scroll value of 20 used for the same reason as mentioned before 
                currentScrollPos = 0 # mentioned before 

                while len(self.contactDict) < self.Forwards:

                    while self.state :

                        for element in elements:

                            if len(self.contactDict) == self.Forwards:
                                self.state = False
                                break

                            try:
                                innerSoup = BeautifulSoup(
                                    element.get_attribute('innerHTML'), features="lxml")
                                rawContactName = innerSoup.div.div.get_text(strip=True)
                                contactName = unicodedata.normalize(
                                    "NFKD", rawContactName)
                                if (not self.contactDict.get(contactName)
                                        and contactName != "New group"):
                                    currentScrollPos = int(self.driver.execute_script(
                                        "return document.querySelector('div._1qDvT._2wPpw').scrollTop"))
                                    message = self.formatMessage(
                                        self.Message, contactName)
                                    element.click()  # Click on the contact
                                    time.sleep(0.1)
                                    try :
                                        self.driver.find_element_by_xpath(
                                            '//div[@class=\'_3uMse\']') # if the contact is blocked there will be no text field and the program handle the NoSuchElementException
                                        self.driver.find_elements_by_xpath(
                                            '//div/div[@class=\'PVMjB\' and 2]')[1].click()  # Click the Choose Media button
                                        time.sleep(1)
                                        imageBtn = self.driver.find_elements_by_xpath(
                                            '//button[@class=\'_1dxx-\']')[0] # click the image Option from the listed media options 
                                        time.sleep(1)
                                        imageInput = imageBtn.find_element_by_tag_name(
                                                                                    'input') # get the image HTML input
                                        imageInput.send_keys(
                                            self.ImagePath)  # send the specified image path to the fetched image input
                                        time.sleep(2) 
                                        textInput = self.driver.find_elements_by_xpath(
                                            '//div[@class=\'_3FRCZ copyable-text selectable-text\']')[0] # this is the text input 
                                        # text to send goes here
                                        textInput.send_keys(message) # nothing will be written if the message is empty
                                        time.sleep(0.1) 
                                        if self.withDelay : 
                                            time.sleep(random.randint(30,60))
                                        if not self.isPreviewMode:
                                            self.driver.find_element_by_xpath(
                                                '//div[@class=\'_3y5oW _3qMYG\']').click()  # This is the Send Button
                                        self.contactDict[contactName] = 1
                                        self.addContact([contactName])
                                        self.strContactSignal.emit(contactName)
                                        self.updatePBsignal.emit(len(self.contactDict))
                                        time.sleep(1)
                                    
                                    except exceptions.NoSuchElementException as e :
                                        self.contactDict[contactName] = 1 # contact was blocked and the input field was not found
                                        pass
                                    time.sleep(0.1)
                                    self.driver.find_elements_by_xpath(
                                        '//div[@class=\'PVMjB\']')[1].click()
                                    time.sleep(0.1)
                                    self.driver.execute_script(
                                        f"document.querySelector('div._1qDvT._2wPpw').scrollTop += {currentScrollPos-200}")
                                    time.sleep(0.1)
                                    elements = self.driver.find_elements_by_xpath(
                                        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')

                                else:
                                    self.driver.execute_script(
                                        f"document.querySelector('div._1qDvT._2wPpw').scrollTop += {scrollValue}")
                                    elements = self.driver.find_elements_by_xpath(
                                        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')

                            except exceptions.StaleElementReferenceException as e:
                                pass

        elif(self.MODE == variables.IMPORTED_NAMES): # here we're dealing with imported names 
            if (self.ImagePath == ""):
                time.sleep(1)
                self.driver.find_elements_by_xpath(
                    '//div[@class=\'PVMjB\']')[1].click()
                time.sleep(0.2)
                elements = self.driver.find_elements_by_xpath(
                    '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')
                scrollValue = 20
                currentScrollPos = 0
                iterator = 0 # this is an iterator used to check how many contacts were scanned from the imported names
                while iterator < len(self.contactDict):

                    while self.state :

                        for element in elements:

                            if iterator == len(self.contactDict):
                                self.state = False
                                break

                            try:
                                innerSoup = BeautifulSoup(
                                    element.get_attribute('innerHTML'), features="lxml")
                                rawContactName = innerSoup.div.div.get_text(strip=True)
                                contactName = unicodedata.normalize(
                                    "NFKD", rawContactName)
                                if (self.contactDict.get(contactName)
                                        and contactName != "New group"): # here we do the inverse of what we did with new names (so if the name is in the hashmap of the imported names send the message)
                                    currentScrollPos = int(self.driver.execute_script(
                                        "return document.querySelector('div._1qDvT._2wPpw').scrollTop"))
                                    time.sleep(0.1)
                                    message = self.formatMessage(
                                        self.Message, contactName)
                                    print(
                                        "\nContact : "+contactName,
                                        "\nMessage : "+message)
                                    element.click()
                                    time.sleep(0.1)
                                    try :
                                        self.driver.find_element_by_xpath(
                                            '//div[@class=\'_3uMse\']').send_keys(message)
                                        time.sleep(0.1)
                                        if self.withDelay : 
                                            time.sleep(random.randint(30,60))
                                        if not self.isPreviewMode:
                                            self.driver.find_element_by_xpath(
                                                '//button[@class=\'_1U1xa\']/span[1]').click() #send button
                                        self.contactDict[contactName] = 0 # Pop the name from the hash map, so that it won't return True when checking for it in the hashmap.get()
                                        iterator = iterator+1 # increment the iterator 
                                        self.addContact([contactName])
                                        self.strContactSignal.emit(contactName)
                                        self.updatePBsignal.emit(iterator)
                                        time.sleep(0.1)
                                    except exceptions.NoSuchElementException as e :
                                        self.contactDict[contactName] = 1 # contact was blocked and the input field was not found
                                        pass

                                    self.driver.find_elements_by_xpath(
                                        '//div[@class=\'PVMjB\']')[1].click()
                                    time.sleep(0.1)
                                    self.driver.execute_script(
                                        f"document.querySelector('div._1qDvT._2wPpw').scrollTop += {currentScrollPos-200}")
                                    time.sleep(0.1)
                                    elements = self.driver.find_elements_by_xpath(
                                        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')

                                else:
                                    self.driver.execute_script(
                                        f"document.querySelector('div._1qDvT._2wPpw').scrollTop += {scrollValue}")
                                    elements = self.driver.find_elements_by_xpath(
                                        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')

                            except (exceptions.StaleElementReferenceException, exceptions.NoSuchElementException, exceptions.JavascriptException) as e:
                                pass  # Same contact element was read, or contact was blocked and the input field was not found

            else: # here the user has specified an image path
                time.sleep(1)
                self.driver.find_elements_by_xpath(
                    '//div[@class=\'PVMjB\']')[1].click()
                time.sleep(0.2)
                elements = self.driver.find_elements_by_xpath(
                    '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')
                scrollValue = 20
                currentScrollPos = 0
                iterator = 0

                while iterator < len(self.contactDict):

                    while self.state :

                        for element in elements:

                            if iterator == len(self.contactDict):
                                self.state = False
                                break


                            try:
                                innerSoup = BeautifulSoup(
                                    element.get_attribute('innerHTML'), features="lxml")
                                rawContactName = innerSoup.div.div.get_text(strip=True)
                                contactName = unicodedata.normalize(
                                    "NFKD", rawContactName)
                                if (self.contactDict.get(contactName)
                                        and contactName != "New group"):
                                    currentScrollPos = int(self.driver.execute_script(
                                        "return document.querySelector('div._1qDvT._2wPpw').scrollTop"))
                                    message = self.formatMessage(
                                        self.Message, contactName)
                                    element.click()  # Click on the contact
                                    time.sleep(0.1)
                                    try :
                                        self.driver.find_element_by_xpath(
                                            '//div[@class=\'_3uMse\']') # if the contact is blocked there will be no text field and the program handle the NoSuchElementException
                                        self.driver.find_elements_by_xpath(
                                            '//div/div[@class=\'PVMjB\' and 2]')[1].click()  # Send Media button
                                        time.sleep(1)
                                        imageBtn = self.driver.find_elements_by_xpath(
                                            '//button[@class=\'_1dxx-\']')[0]
                                        time.sleep(1)
                                        imageInput = imageBtn.find_element_by_tag_name(
                                                                                    'input')
                                        imageInput.send_keys(
                                            self.ImagePath)  # Path to media
                                        time.sleep(2)
                                        textInput = self.driver.find_elements_by_xpath(
                                            '//div[@class=\'_3FRCZ copyable-text selectable-text\']')[0]
                                        # text to send goes here
                                        textInput.send_keys(message)
                                        time.sleep(0.1)
                                        if self.withDelay : 
                                            time.sleep(random.randint(30,60))
                                        if not self.isPreviewMode:
                                            self.driver.find_element_by_xpath(
                                                '//div[@class=\'_3y5oW _3qMYG\']').click()  # This is the Send Button
                                        self.contactDict[contactName] = 0
                                        iterator = iterator+1
                                        self.addContact([contactName])
                                        self.strContactSignal.emit(contactName)
                                        self.updatePBsignal.emit(iterator)
                                        time.sleep(1)
                                    
                                    except exceptions.NoSuchElementException as e :
                                        self.contactDict[contactName] = 1 # contact was blocked and the input field was not found
                                        pass

                                    self.driver.find_elements_by_xpath(
                                        '//div[@class=\'PVMjB\']')[1].click()
                                    time.sleep(0.1)
                                    self.driver.execute_script(
                                        f"document.querySelector('div._1qDvT._2wPpw').scrollTop += {currentScrollPos-200}")
                                    time.sleep(0.1)
                                    elements = self.driver.find_elements_by_xpath(
                                        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')

                                else:
                                    self.driver.execute_script(
                                        f"document.querySelector('div._1qDvT._2wPpw').scrollTop += {scrollValue}")
                                    elements = self.driver.find_elements_by_xpath(
                                        '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')

                            except exceptions.StaleElementReferenceException as e:
                                pass

    def setForwards(self, val): # set the number of desired forwards  
        self.Forwards = int(val) # value received is a string, convert it to int 

    def setImagePath(self, val): # set the path of an image if specified
        self.ImagePath = str(val)

    def setContactsType(self, val): # set the MODE (NEW NAMES or IMPORTED NAMES)
        self.contactsType = int(val)

    def setContactDict(self, cdict): # set the contact hashmap (if we're loading from a record, this will hold the names of the alreday scanned contacts, if we're dealing with imported names, this will return the list of imported contact names to scan)
        self.contactDict = cdict

    def setPreviewMode(self, pbool): # value of the preview mode checkbox
        self.isPreviewMode = pbool

    def setMessage(self, msg): # setting the message to send 
        self.Message = msg

    def addContact(self, name): # add the contact name to the csv file everytime a new contact is scanned, this function loads the file, writes to it and saves it everytime, thus if any runtime error occurs, the data will not be affected 
        csvFile = open(f'records/{self.fileName}/record.csv', 'a') # open the file 
        writer = csv.writer(csvFile) # load the writer
        writer.writerow(name) # write the name to teh file
        csvFile.close() # save the file and close 

    def loadCsvFile(self): # create the csv file if we're not working with a previous record 
        csvFile = open(f'records/{self.fileName}/record.csv', 'w+') # create the file 
        writer = csv.writer(csvFile) # init the writer
        writer.writerow(["Name"]) # write the Name column
        csvFile.close() # save and close the file 

    def setFileName(self, name): # set the record name if we're loading a previous record 
        self.fileName = name
    
    def setContactMode(self, mode): # setting the MODE (NEW NAMES or IMPORTED NAMES)
        self.MODE = mode

    def setIsDelayMode(self, withDelay): # get value from the delay checkbox
        self.withDelay = withDelay

    def formatMessage(self, msg, contactName): # before we send the message, we must format it
        msg = msg.replace("\n", Keys.SHIFT+Keys.ENTER+Keys.SHIFT) # if there are new lines in the message, the browser reads them as a SEND message command, so here we replace thos new line chars with special commands that let us jump into a new line in the input
        if ('###' in msg):
            # The input is sometimes skipping the first character so there is
            # an extra space at start just in case
            return " "+msg.replace("###", contactName) # we replace every occurence of ### with the name of the current contact name  
        return msg # return the formatted message 

    def loadWebsite(self): # load the website first 
        self.driver = webdriver.Chrome(ChromeDriverManager().install()) # if there is no chrome driver installed (first time runnig the program), the program will automatically fetch it and download it then open it 
        self.driver.get("https://web.whatsapp.com/") # load the whatsapp web site 


