from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib import request
import time
import re
import itertools
import pandas as pd
import os
from datetime import datetime
from urllib import parse

CHROMEDRIVER_PATH = os.environ['CHROMEDRIVER_PATH']

BASE_URL = "https://www.olx.co.id"
HOME_URL = BASE_URL + "/mobil-bekas_c198"
FILTER_PARAM = "?filter="

# example filter extension = ?filter=m_color_eq_hitam%2Cm_fuel_eq_bensin%2Cm_seller_type_eq_seller-type-individu%2Cm_transmission_eq_manual%2Cmileage_eq_45
# format : mileage_eq_130_and_135_and_200
mileage_list = [
    [45, 55, 35, 30, 105], [40, 25, 20, 50, 15], [65, 5, 60, 75, 100], [70, 85, 10, 80, 95], [90, 110, 115, 120, 125], [301, 130, 155, 135, 150], [145, 205, 140, 160, 165], [200, 175, 170, 180, 185], [195, 190, 210, 300, 215], [225, 220, 255, 230, 235], [245, 250, 240, 260, 285], [275, 265, 280, 295, 270, 290]
]

mileage = ['_and_'.join(map(str, mil)) for mil in mileage_list]

# format : m_fuel_eq_bensin_and_diesel
fuel = [
    "bensin", "diesel", "hybrid", "listrik"
]

# format : m_transmission_eq_manual_and_automatic_and_triptonic
transmission = [
    "manual", "automatic", "tritonic"
]

# format : m_seller_type_eq_seller-type-individu_and_seller-type-diler
seller_type = [
    "seller-type-individu", "seller-type-diler"
]

# format : m_color_eq_hitam_and_putih_and_silver_and_abu-abu_and_merah_and_ungu_and_biru_and_hijau_and_coklat_and_lainnya_and_marun_and_kuning_and_oranye_and_emas
color = [
    "hitam", "putih", "silver", "abu-abu", "merah", "ungu", "biru", "hijau", "coklat", "lainnya", "marun", "kuning", "oranye", "emas"
]

filters = [mileage, fuel, transmission, seller_type, color]

filter_keys = {
    0: "mileage_eq_", 1: "m_fuel_eq_", 2: "m_transmission_eq_", 3: "m_seller_type_eq_", 4: "m_color_eq_"
}

def generate_url_combinations():
    filter_combination = list(itertools.product(*filters))
    params = []
    for combi in filter_combination:
        combi_param = [filter_keys[idx] + str(value) for idx, value in enumerate(combi)]
        params.append('%2C'.join(combi_param))
    url = HOME_URL + FILTER_PARAM
    return [url + param for param in params]

def get_full_page_source(url):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options)
    driver.get(url)
    while True:
        button_list = driver.find_elements_by_xpath("//button[@data-aut-id='btnLoadMore']")
        if button_list == []: break
        button_list[0].click()
        time.sleep(2)
    return driver.page_source

def get_urls_per_page(page_source):
    soup = BeautifulSoup(page_source, features="html.parser")
    links = []
    for li in soup.find_all('li', attrs={"data-aut-id": True}):
        link = li.find('a').get('href')
        links.append(BASE_URL + link)
    return links

def scrape_car_detail(page_url):
    print('-- Scraping Car Detail', page_url)

    page_source = request.urlopen(page_url)
    page_soup = BeautifulSoup(page_source, features="html.parser")

    car_detail = {}
    detail_soup = page_soup.find("div", class_="_3JPEe")
    for soup in detail_soup:
        key = soup.find(attrs={"data-aut-id": re.compile(r'key_*')}).text

        values = soup.find_all(attrs={"data-aut-id": re.compile(r'value_*')})
        if values != None:
            values = [val.text for val in values]
        if len(values) == 1:
            values = values[0] 
        elif len(values) == 0:
            values = ''
    
        car_detail[key] = values
    
    title_soup = page_soup.find("section", class_="_2wMiF")
    location = title_soup.find("span", class_="_2FRXm").text
    car_detail['Lokasi'] = location
    price = title_soup.find("span", attrs={"data-aut-id": "itemPrice"}).text
    car_detail['Harga'] = price
    car_detail['Url'] = page_url
    
    return car_detail

def save_into_csv(df, page_url):
    splitted_url = parse.urlparse(page_url)
    file_name = str(datetime.now()) + '_' + splitted_url.path.split('/')[-1] + '.csv'
    output_dir = "./output/"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    output_path = os.path.join(output_dir + file_name)
    df.to_csv(output_path, index = None, header = True)

page_urls = generate_url_combinations()

count = 1
for page_url in page_urls:
    print('- Scraping Cars', page_url, '-', count, '/', len(page_url))
    count += 1
    try:
      page_source = get_full_page_source(page_url)
      urls_per_page = get_urls_per_page(page_source)

      car_details = []
      for url in urls_per_page:
        try:
          car_detail = scrape_car_detail(url)
          car_details.append(car_detail)
        except Exception as e:
          print(" --> Error while scraping car", url)
      
      df = pd.DataFrame(car_details)
      save_into_csv(df, page_url)
    except Exception as e:
      print("Error type: " + str(e))