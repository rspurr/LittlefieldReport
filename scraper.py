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

    def __init__(self, driver_path, user, pw):

        options = Options()
        options.add_argument("--headless")  # run chrome in headless mode
        driver_path = driver_path
        self.driver = webdriver.Chrome(executable_path=driver_path,
                                       chrome_options=options)

        self.user = user
        self.pw = pw

        self.pages = {
            'login' : "http://op.responsive.net/lt/groenevelt/entry.html",
            'orders': "http://op.responsive.net/Littlefield/OrdersMenu",
            'order_data' : "http://op.responsive.net/Littlefield/Plot?data=JOBIN&x=all",
            'materials': "http://op.responsive.net/Littlefield/MaterialMenu",
            'inv_data' :"http://op.responsive.net/Littlefield/Plot?data=INV&x=all",
            "s1queue"   : "http://op.responsive.net/Littlefield/Plot?data=S1Q&x=all",
            "s2queue"   : "http://op.responsive.net/Littlefield/Plot?data=S2Q&x=all",
            "s3queue"   : "http://op.responsive.net/Littlefield/Plot?data=S3Q&x=all"
        }

    def run(self):
        self.do_login()
        self.get_order_info()
        self.get_materials_info()
        self.get_queues()
        os.system("TASKKILL /F /IM chromedriver.exe >nul 2>&1") # force kill chromedriver instance, driver.quit() broke
        print "\n[+] Scraping complete!"

    def do_login(self):
        self.driver.get(self.pages['login'])

        print "[+] Logging in..."

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


        order_data = self.scrape_table_data(category="order_data")

        print order_data

    def scrape_table_data(self, category):

        self.driver.get(self.pages[category])

        self.driver.find_element_by_name("data").click()

        table_data =  {"type": category,
                      "days": [],
                      "data": []}

        bs = BeautifulSoup(self.driver.page_source, "html.parser")

        # scrape js and find data section

        regex = "([0-9]* [0-9]+\.*[0-9]*)*"

        script = bs.find_all("script")
        pattern = re.compile("points: '" + regex)
        data = pattern.search(str(script))
        data_str = data.group(0)[9:]

        # use regex to find repeating numbers, ints or floats
        repeating_regex = "[0-9]+ [0-9]+\.*[0-9]*"

        match_ptrn = re.compile(repeating_regex)
        matches = match_ptrn.findall(data_str)

        for match in matches:
            # split pairs into respective arrays
            grp_regex = "([0-9]+) ([0-9]+\.*[0-9]*)"

            group_ptrn = re.compile(grp_regex)
            groups = group_ptrn.match(match)

            table_data['days'].append(groups.group(1))
            table_data['data'].append(groups.group(2))

        return table_data

    def get_materials_info(self):
        self.driver.get(self.pages['materials'])

        html = self.driver.page_source
        bs = BeautifulSoup(html, "html.parser")

        # find materials data in html

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

        inv_data = self.scrape_table_data(category="inv_data")

        print inv_data

    def get_queues(self):
        print "[+] Getting queue data..."

        s1q = self.scrape_table_data(category="s1queue")
        s2q = self.scrape_table_data(category="s2queue")
        s3q = self.scrape_table_data(category="s3queue")

        print s1q
        print s2q
        print s3q

if __name__ == "__main__":
    print "[+] Initiating Littlefield Data Scraping..."

    scraper = Scraper(driver_path="",
                      user="",
                      pw="")
    scraper.run()

