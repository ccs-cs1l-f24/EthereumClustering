import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import csv

link_file = "dex_links.csv"
out_file = "dex_data.csv"

addr_links = []

# extract links and exchange names
with open(link_file, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        addr_links.append(row[0])

print("Exchanges:", len(addr_links))

# desired information in final: exchange name, address, account type
addr_list = []
account_type = []
exch_names = []

service = Service("/snap/bin/firefox.geckodriver")

with open(out_file, 'w') as out:
    for url in addr_links:
        driver = webdriver.Firefox(service=service)
        driver.get(url)
        time.sleep(3)

        html = driver.page_source

        soup = BeautifulSoup(html, "html.parser")

        try:
            address = soup.find(id="mainaddress")
        except:
            address = "null"

        # add_type is 1 if contract, 0 if address, -1 otherwise
        try:
            add_type = soup.find_all("h1", {"class": "h5 mb-0"})[0]
        except:
            add_type = "null"

        try:
            result = soup.find_all('div', {"class": "d-flex align-items-center gap-1 mt-2"})
            addr_name = result[0].get_text(strip=True)
        except:
            addr_name = "null"

        csvwriter = csv.writer(out)
        csvwriter.writerow([addr_name[0:addr_name.rfind("(")], address.string, add_type.string.split()[0]])

        driver.close()

print("Complete!")