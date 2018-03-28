import os, sys, time, re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import pandas as pd


class Scraper:

    def __init__(self):
        self.web = webdriver.Chrome
        options = Options()
        options.add_argument("--headless")
        options.binary_location = "C:\\Users\\ryan\\AppData\\Local\\Google\\Chrome SxS\\Application\\chrome.exe"
        driver_path = "C:\\Users\\ryan\\Desktop\\chromedriver_win32\\chromedriver.exe"
        self.driver = webdriver.Chrome(executable_path=driver_path,
                                       chrome_options=options)

        self.user = "wealreadywon"
        self.pw = "mijury"

        self.pages = {
            'login' : "http://op.responsive.net/lt/groenevelt/entry.html",
            'orders': "http://op.responsive.net/Littlefield/OrdersMenu",
            'order_data' : "http://op.responsive.net/Littlefield/Plot?data=JOBIN&x=all",
            'materials': "http://op.responsive.net/Littlefield/MaterialMenu",
            'inv_data' :"http://op.responsive.net/Littlefield/Plot?data=INV&x=all"
        }

    def run(self):
        self.do_login()
        self.get_order_info()
        self.get_materials_info()
        os.system("TASKKILL /F /IM chromedriver.exe >nul 2>&1")
        print "\n[+] Scraping complete!"

    def do_login(self):
        self.driver.get(self.pages['login'])

        print "[+] Logging in..."

        html = self.driver.page_source

        user = self.driver.find_element_by_name("id")
        user.click()
        user.send_keys(self.user)

        pw = self.driver.find_element_by_name("password")
        pw.click()
        pw.send_keys(self.pw)
        pw.submit()

        time.sleep(5)

        if self.driver.title == "Littlefield":
            print "[+] Logged in! Beginning scraping..."
            self.get_basics()

    def get_basics(self):

        element = WebDriverWait(self.driver, 5).until(EC.frame_to_be_available_and_switch_to_it("IDbox"))
        if element:
            html = self.driver.page_source
            bs = BeautifulSoup(html, "html.parser")
            day = bs.find("b", text="Day: ")
            day = day.next_sibling

            cash = bs.find("b", text="Cash Balance: ")
            cash = cash.next_sibling

            print "\n[+] Day: {}\n[+] Cash: ${}".format(day.strip("\n"), cash.strip("\n"))

        else:
            raise Exception("Element doesn't exist")

    def get_order_info(self):

        self.driver.get(self.pages['orders'])

        html = self.driver.page_source
        bs = BeautifulSoup(html, "html.parser")

        print "\n--- Order Info ---\n"
        max_wip_limit = bs.find("b", text="Maximum WIP Limit: ").next_sibling
        print "[+] Max WIP Limit: {}".format(max_wip_limit)
        num_kits = bs.find("b", text="Number of kits in 1 job: ").next_sibling
        print "[+] Num Kits per Job: {}".format(num_kits)
        lot_size = bs.find("b", text="Lot size: ").next_sibling
        print "[+] Lot size: {}".format(lot_size)
        curr_contract = bs.find("b", text="Current contract: ").next_sibling
        print "[+] Current contract: {}".format(curr_contract)

        order_data = {"days": [],
                      "data": []}

        self.driver.get(self.pages['order_data'])

        self.driver.find_element_by_name("data").click()

        html = self.driver.page_source
        bs = BeautifulSoup(html, "html.parser")

        # scrape js and find data section

        script = bs.find_all("script")
        pattern = re.compile("points: '([0-9]* [0-9]*)*")
        data = pattern.search(str(script))
        data_str = data.group(0)
        data_str = data_str[9:]

        # use regex to find repeating numbers

        match_ptrn = re.compile("[0-9]+ [0-9]+")
        matches = match_ptrn.findall(data_str)

        for match in matches:
            group_ptrn = re.compile("([0-9]+) ([0-9]+)")
            groups = group_ptrn.match(match)

            order_data['days'].append(groups.group(1))
            order_data['data'].append(groups.group(2))

        print order_data

    def get_materials_info(self):
        self.driver.get(self.pages['materials'])

        html = self.driver.page_source
        bs = BeautifulSoup(html, "html.parser")

        print "\n--- Materials Info ---\n"
        unit_cost = bs.find("b", text="Unit Cost: ").next_sibling.strip("\n")
        print "[+] Unit Cost: {}".format(unit_cost)
        order_cost = bs.find("b", text="Order Cost: ").next_sibling.strip("\n")
        print "[+] Order Cost: {}".format(order_cost)
        lead_time = bs.find("b", text="Lead Time:").next_sibling.strip("\n")
        print "[+] Lead Time: {}".format(lead_time)
        reorder_pt = bs.find("b", text="Reorder Point:").next_sibling.replace("\n", " ")
        print "[+] Reorder Point: {}".format(reorder_pt)
        order_q = bs.find("b", text="Order Quantity:").next_sibling.replace("\n", " ")
        print "[+] Order Quantity: {}".format(order_q)

        self.driver.get(self.pages['inv_data'])

        self.driver.find_element_by_name("data").click()

        html = self.driver.page_source
        bs = BeautifulSoup(html, "html.parser")

        script = bs.find_all("script")

        # scrape js and find data section

        pattern = re.compile("points: '([0-9]* [0-9]*)*")
        data = pattern.search(str(script))
        data_str = data.group(0)
        data_str = data_str[9:]

        # use regex to find repeating numbers

        match_ptrn = re.compile("[0-9]+ [0-9]+")
        matches = match_ptrn.findall(data_str)

        inv_data = {"days": [],
                    "data": []}

        # get groups of numbers and add to respective arrays

        for match in matches:
            group_ptrn = re.compile("([0-9]+) ([0-9]+)")
            groups = group_ptrn.match(match)

            inv_data['days'].append(groups.group(1))
            inv_data['data'].append(groups.group(2))

        print inv_data


if __name__ == "__main__":
    print "[+] Initiating Littlefield Data Scraping..."

    scraper = Scraper()
    scraper.run()

