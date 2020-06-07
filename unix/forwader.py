from PyQt5.QtCore import QThread
from PyQt5 import uic, Qt, QtWidgets, QtCore
from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.common import exceptions
import unicodedata
import os
import json
import csv
import selenium

class WhatsappForwader(QThread):

    strContactSignal = QtCore.pyqtSignal(str, name="strSignal")
    updatePBsignal = QtCore.pyqtSignal(int, name="intSignal")

    def __init__(self):
        super(WhatsappForwader, self).__init__()
        self.state = True
        self.contactDict = {}
        self.AllContacts = []
        self.isPreviewMode = True

    def run(self):

        if (self.ImagePath == ""):
            time.sleep(1)
            self.driver.find_elements_by_xpath(
                '//div[@class=\'PVMjB\']')[1].click()
            time.sleep(0.2)
            elements = self.driver.find_elements_by_xpath(
                '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')
            scrollValue = 20
            currentScrollPos = 0

            while len(self.contactDict) < self.Forwards:

                for element in elements:

                    if len(self.contactDict) == self.Forwards:
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
                                if not self.isPreviewMode:
                                    self.driver.find_elements_by_xpath(
                                        '//div[@class=\'_1JNuk\']')[1].click()
                                self.contactDict[contactName] = 1
                                self.addContact([contactName])
                                self.strContactSignal.emit(contactName)
                                self.updatePBsignal.emit(len(self.contactDict))
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

        else:
            time.sleep(1)
            self.driver.find_elements_by_xpath(
                '//div[@class=\'PVMjB\']')[1].click()
            time.sleep(0.2)
            elements = self.driver.find_elements_by_xpath(
                '//div[2]/div[1]/div[@class=\'-GlrD _2xoTX\' and 1]/div[@class=\'_210SC\' and 19]/div[1]/div[@class=\'eJ0yJ\' and 1]/div[2]')
            scrollValue = 20
            currentScrollPos = 0

            while len(self.contactDict) < self.Forwards:

                for element in elements:

                    if len(self.contactDict) == self.Forwards:
                        break

                    try:
                        innerSoup = BeautifulSoup(
                            element.get_attribute('innerHTML'), features="lxml")
                        rawContactName = innerSoup.div.div.get_text(strip=True)
                        contactName = unicodedata.normalize(
                            "NFKD", rawContactName)
                        if (not self.contactDict.get(contactName)
                                and contactName != "New group"):
                            message = self.formatMessage(
                                self.Message, contactName)
                            element.click()  # Click on the contact
                            time.sleep(0.1)
                            self.driver.find_elements_by_xpath(
                                '//div/div[@class=\'rAUz7\' and 2]')[1].click()  # Send Media button
                            time.sleep(1)
                            imageBtn = self.driver.find_elements_by_xpath(
                                '//button[@class=\'_1azEi\']')[0]
                            time.sleep(1)
                            imageInput = imageBtn.find_element_by_tag_name(
                                                                           'input')
                            imageInput.send_keys(
                                self.ImagePath)  # Path to media
                            time.sleep(2)
                            textInput = self.driver.find_elements_by_xpath(
                                '//div[@class=\'_2S1VP copyable-text selectable-text\']')[0]
                            # text to send goes here
                            textInput.send_keys(message)
                            time.sleep(0.1)
                            if not self.isPreviewMode:
                                self.driver.find_element_by_xpath(
                                    '//div[@class=\'_3hV1n yavlE\']').click()  # This is the Send Button
                            self.contactDict[contactName] = 1
                            self.addContact([contactName])
                            self.strContactSignal.emit(contactName)
                            self.updatePBsignal.emit(len(self.contactDict))
                            time.sleep(1)
                            self.driver.find_elements_by_xpath(
                                '//div[@class=\'rAUz7\' and 2]/div[1]/span[1]')[1].click()
                            time.sleep(0.3)
                            elements = self.driver.find_elements_by_xpath(
                                '//div[2]/div[1]/div[1]/div[@class=\'_2wP_Y\' and 5]/div[1]/div[@class=\'_2EXPL\' and 1]/div[@class=\'_3j7s9\' and 2]')

                        else:
                            self.driver.execute_script(
                                f"document.querySelector('div._1vDUw._2sNbV').scrollTop += {scrollValue}")
                            elements = self.driver.find_elements_by_xpath(
                                '//div[2]/div[1]/div[1]/div[@class=\'_2wP_Y\' and 5]/div[1]/div[@class=\'_2EXPL\' and 1]/div[@class=\'_3j7s9\' and 2]')

                    except exceptions.StaleElementReferenceException as e:
                        pass

    def stopScraper(self):
        self.state = False

    def setForwards(self, val):
        self.Forwards = int(val)

    def setImagePath(self, val):
        self.ImagePath = str(val)

    def setContactsType(self, val):
        self.contactsType = int(val)

    def setContactDict(self, cdict):
        self.contactDict = cdict

    def setPreviewMode(self, pbool):
        self.isPreviewMode = pbool

    def setMessage(self, msg):
        self.Message = msg

    def addContact(self, name):
        csvFile = open(f'records/{self.fileName}/record.csv', 'a')
        writer = csv.writer(csvFile)
        writer.writerow(name)
        csvFile.close()

    def loadCsvFile(self):
        csvFile = open(f'records/{self.fileName}/record.csv', 'w+')
        writer = csv.writer(csvFile)
        writer.writerow(["Name"])
        csvFile.close()

    def setFileName(self, name):
        self.fileName = name

    def formatMessage(self, msg, contactName):
        if ('###' in msg):
            # The input is sometimes skipping the first character so there is
            # an extra space at start just in case
            return " "+msg.replace("###", contactName)
        return msg

    def loadWebsite(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver.get("https://web.whatsapp.com/")


