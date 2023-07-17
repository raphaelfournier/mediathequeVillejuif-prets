import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from configparser import ConfigParser
import pandas as pd

def lectureConfig(configfile):
    parser = ConfigParser() 
    parser.read(configfile)
    utilisateurs = {}

    for user in parser.sections():
        utilisateurs[user] = {}
        for key, value in parser.items(user):
            utilisateurs[user][key] = value
    return utilisateurs

def getResume(resume):
    elems = resume.find_elements(By.TAG_NAME,"div")

    long = len("Dans 3 jours :")
    for i in elems:
        if i.get_dom_attribute("class") == "valid":
            encours = i.find_element(By.TAG_NAME,"span").text
            print("En cours :".ljust(long), encours)
        if i.get_dom_attribute("class") == "warning":
            troisjours = i.find_element(By.TAG_NAME,"span").text
            print("Dans 3 jours :", troisjours)
        if i.get_dom_attribute("class") == "nonvalid":
            retard = i.find_element(By.TAG_NAME,"span").text
            print("En retard :".ljust(long), retard)
    return (encours, retard)

def extractElements(emprunts):
    notice = emprunts.find_element(By.CLASS_NAME, 'notice')
    elements = notice.find_elements(By.TAG_NAME,"li")
    for doc in elements:
        if "loan-item" in doc.get_dom_attribute("class"):
            e = doc.find_element(By.CLASS_NAME,"loan-custom-result")
            titre = e.find_element(By.TAG_NAME, "h3").text
            print(titre)

            infowrap = doc.find_element(By.CLASS_NAME,"additional-infos-wrapper")
            infos = infowrap.find_elements(By.TAG_NAME,"li")
            for info in infos:
                if "localisation" in info.get_dom_attribute("class"):
                    localisation = info.find_element(By.CLASS_NAME,"loan-info-value").text
                if "dateretour" in info.get_dom_attribute("class"):
                    dateretour = info.find_element(By.CLASS_NAME,"loan-info-value").text
            print("  ", localisation, dateretour)

def storeElements(emprunts, statut):
    mydic = {}
    notice = emprunts.find_element(By.CLASS_NAME, 'notice')
    elements = notice.find_elements(By.TAG_NAME,"li")
    for doc in elements:
        if "loan-item" in doc.get_dom_attribute("class"):
            e = doc.find_element(By.CLASS_NAME,"loan-custom-result")
            titre = e.find_element(By.TAG_NAME, "h3").text
            # print(titre)

            infowrap = doc.find_element(By.CLASS_NAME,"additional-infos-wrapper")
            infos = infowrap.find_elements(By.TAG_NAME,"li")
            for info in infos:
                if "holdingid" in info.get_dom_attribute("class"):
                    codebarre = info.find_element(By.CLASS_NAME,"loan-info-value").text
                if "localisation" in info.get_dom_attribute("class"):
                    localisation = info.find_element(By.CLASS_NAME,"loan-info-value").text
                if "dateretour" in info.get_dom_attribute("class"):
                    dateretour = info.find_element(By.CLASS_NAME,"loan-info-value").text
            # print("  ", localisation, dateretour)
            mydic[codebarre] = {}
            mydic[codebarre]["titre"] = titre
            mydic[codebarre]["date"] = dateretour
            mydic[codebarre]["localisation"] = localisation
    return mydic


def pretsUtilisateur(utilisateur):
    dicoprets = {}
    username = utilisateur["username"]
    password = utilisateur["password"]

    url = "https://mediatheque.villejuif.fr/"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    connexBtn = driver.find_element("id","dropMenu1")
    connexBtn.click()

    un = driver.find_element("name", "name")
    un.send_keys(username)
    pw = driver.find_element("name", "pwd")
    pw.send_keys(password)
    un.submit()

    accountBtn = driver.find_element("id","dropMenu1")
    accountBtn.click()

    time.sleep(3)

    url = "https://mediatheque.villejuif.fr/Default/my-account.aspx"
    driver.get(url)

    time.sleep(3)
    try:
        # mesprets = WebDriverWait(driver, 3).until( EC.presence_of_element_located((By.CLASS_NAME, 'ui-loans-active')))
        mesprets = driver.find_element(By.CLASS_NAME, 'ui-loans-active')
        mesprets.click()
    except NoSuchElementException:
        print("active loans non trouvé")
        exit(1)

    time.sleep(2)

    # summary
    summary = driver.find_element(By.CLASS_NAME, 'details-wrapper')
    encours, retard = getResume(summary)

    time.sleep(1)

    try:
        prets = driver.find_element(By.ID, 'loans-box')
    except NoSuchElementException:
        print("loans-box non trouvé")
        exit(1)

    if int(encours) > 0:
        # print("==========================")
        # print("\nEn cours :")
        # extractElements(prets)
        dicoprets = storeElements(prets,"encours")
        # print("==========================")

    time.sleep(2)

    if int(retard) > 0:

        boutonRetard = driver.find_element(By.ID, 'ui-loans-late')
        boutonRetard.click()

        time.sleep(2)
        try:
            retards = driver.find_element(By.ID, 'loans-late-box')
        except NoSuchElementException:
            print("loans-late-box non trouvé")
            exit(1)

        # print("\n==========================")
        # print("En retard :")
        # extractElements(retards)
        dicoprets = {**dicoprets, **storeElements(retards, "retard")}
        # print("==========================\n")

        time.sleep(2)

    df = pd.DataFrame(columns=['date', 'lieu', 'titre', 'code'])
    l = []
    for k,v in dicoprets.items():
        d = {}
        d["code"] = k
        for c,b in v.items():
            d[c] = b
        l.append(d)
    df = pd.DataFrame.from_records(l)

    print(df.to_markdown())

    return dicoprets

if __name__ == '__main__':
    utilisateurs = lectureConfig("config.ini")
    pretsAll = {}
    for user, infouser in utilisateurs.items():
        print("*** Utilisateur:",user,"***")
        error_counter = 0
        try:
            pretsAll[user] = pretsUtilisateur(infouser)
        except:
            if error_counter < 3:
                error_counter += 1
                print("it failed "+str(error_counter)+" time(s). Restarting...")
                pretsUtilisateur(infouser)
            else:
                raise Exception("3 errors. Stopping")
