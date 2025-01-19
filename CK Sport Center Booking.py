from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidSelectorException, NoSuchElementException
import time
from win11toast import notify
from enum import Enum


SEARCH_DELAY = 300 # 5 minutes

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--log-level=1')
driver = webdriver.Chrome(options=options)
driver.maximize_window()
#driver.implicitly_wait(10)
#driver = webdriver.Chrome()

#region Constants And Globals
CLASS = "week-box"
# endregion

# region Class    
class Slot:
  def __init__(self, hour1, hour2):
    self.hour1 = hour1
    self.hour2 = hour2
    self.pageWhereIsAvailable = None
    
class Session:
  def __init__(self, slots: List[Slot], date):
    self.slots = slots
    self.date = date

class Sport(Enum):
    Badminton = 1
    Padel = 2
# endregion
    
# region Functions

def searchAvailableSlot(slot: Slot, date, page):
    try:
        xpath = "/html/body/div[7]/article/div[7]/div/table/tbody/tr[" + str(locateSlotRow(slot)) + "]/td[2]"
        slotElement = driver.find_element(By.XPATH, xpath)
        courts = slotElement.find_elements(By.CLASS_NAME, CLASS)
        for court in courts:
            if court.get_attribute("class") == CLASS:
                slot.pageWhereIsAvailable = page
                print("   => Court", court.text,"|", displaySlot(slot), "|", date)
    except:
        pass
    
def getSport(sportNumber) -> Sport:
    for sport in [sport for sport in Sport]:
        if sportNumber == int(sport.value):
            return sport

def displaySlot(slot: Slot):
    return slot.hour1 + " - " + slot.hour2

def locateSlotRow(slot: Slot):
    tableRows = driver.find_elements(By.XPATH, "//tbody//tr")
    slotRow = driver.find_element(By.XPATH, "//nobr[contains(text(), '"+slot.hour1+"') and contains(text(), '"+slot.hour2+"')]").find_element(By.XPATH, "..").find_element(By.XPATH, "..")
    return tableRows.index(slotRow) - 2
    
def getSessionsInput(dates) -> List[Session]:
    sessions = []
    for date in dates:
        slotCount = int(input("Nombre de sessions pour le " + date + " : "))
        slots = []
        for i in range(slotCount):
            hour1 = formatHour(input("Heure début session " + str(i+1) + " (hh:mm ou hh) : "))
            hour2 = formatHour(input("Heure fin session " + str(i+1) + " (hh:mm ou hh) : "))
            print("=>", hour1, hour2)
            slots.append(Slot(hour1, hour2))
        sessions.append(Session(slots, date))
    return sessions

def formatHour(hour):
    if len(hour) == 2:
        return hour + ":00"
    elif len(hour) == 1:
        return "0" + hour + ":00"
    else:
        return hour
        
def displayToast(slot: Slot, date):
    try:
        message = "Terrain trouvé pour le " + date + " à " + displaySlot(slot)
        url = ""
        if(sportInput == Sport.Badminton):
            url = "https://ck-sportcenter.lu/reservations_week.php?action=showReservations&type_id=2&date=" + date + "&page=1"
        else:
            url = "https://ck-sportcenter.lu/reservations_week.php?action=showReservations&type_id=4&date=" + date + "&page=" + str(slot.pageWhereIsAvailable)
        notify("BDM Booking Tool", 
                message, 
                #icon="badminton.ico", 
                duration="long",
                button={'activationType': 'protocol', 'arguments': url, 'content': 'Réserver'})
    except:
        pass

def displaySearch(sessions: List[Session]):
    print("\n\n*** Paramètres de recherche ***")
    for session in sessions:
        print("  *", session.date)
        for slot in session.slots:
            print("    -", displaySlot(slot))

def isAllFound(sessions: List[Session]):
    for session in sessions:
        for slot in session.slots:
            if slot.pageWhereIsAvailable == None:
                return False
    return True
            
# endregion

print("**************************")
print("         BAD BOT          ")
print("**************************")

# region Inputs  
datesInput = input("Dates (AAAA-MM-JJ) séparés par une virgule : ").split(",")
sportInput = getSport(input("Sport (1 => Badminton, 2 => Padel) : "))
sessionsInput = getSessionsInput(datesInput)
# endregion

# region Search
displaySearch(sessionsInput)
print("\n\n****** Début de la recherche ******")
while not isAllFound(sessionsInput):
    for session in sessionsInput:
        for slot in session.slots:
            print("\n*** Recherche de session ***\n", displaySlot(slot), "le", session.date, "\n")
            if(sportInput == Sport.Badminton):
                driver.get("https://ck-sportcenter.lu/reservations_week.php?action=showReservations&type_id=2&date=" + session.date + "&page=1")
            else:
                driver.get("https://ck-sportcenter.lu/reservations_week.php?action=showReservations&type_id=4&date=" + session.date + "&page=2")
                searchAvailableSlot(slot, session.date, 2)
                driver.get("https://ck-sportcenter.lu/reservations_week.php?action=showReservations&type_id=4&date=" + session.date + "&page=1")
            searchAvailableSlot(slot, session.date, 1)
            if slot.pageWhereIsAvailable != None:
                displayToast(slot, session.date) 
            else:
                print("Aucun terrain disponible.")
    if not isAllFound(sessionsInput):
        print("\n\nIl manque des terrains.\nNouvelle recherche dans", str(SEARCH_DELAY/60), "minutes...\n\n")
        time.sleep(SEARCH_DELAY)
# endregion

print("Fin de la recherche.")
driver.quit()
time.sleep(500)