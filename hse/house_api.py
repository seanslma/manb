# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: p12
#     language: python
#     name: python3
# ---

# ## Introduction
#
# This notebook will document the creation of a real estate price and information dataset. 
# I will use packages BeautifulSoup and Selenium to scrape data from realestate.com.au and domain.com.au and then process it into a structured dataset for modelling.

import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import sys
import numpy as np
import pandas as pd
import regex as re
import requests
from math import ceil
from time import sleep, time, perf_counter
from random import randint
from IPython.display import clear_output
from fake_useragent import UserAgent
from datetime import datetime

headersx = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}
headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0'}

import os
print(os.path.expanduser("~"))

# ## Get page links
# Open the Firefox browser and go to website using Selenium

# +
onthehouse_url = 'https://www.onthehouse.com.au'
onthehouse_path = '/property/qld/north-lakes-4509?bedsMin=5&soldHistory=false&rentedHistory=true&types=House&sort=dateSoldNewest'

browser = webdriver.Firefox()
browser.get(f'{onthehouse_url}{onthehouse_path}') #&page=2
# -

# First we need to inspect the HTML of the site to look for the tags which store the links to the detailed property information pages. Let's use BeautifulSoup to scrape the page's HTML and telling it to find that details link for each property.

soup = BeautifulSoup(browser.page_source, 'html.parser')
page_tags = soup.find_all('a', class_='page-link Pagination__pagelink--3V5Te')
page_hrefs = []
for tag in page_tags:
    txt = tag.string
    if txt is not None:
        page_hrefs.append(tag['href'])
page_hrefs = list(set(page_hrefs))
page_hrefs

test_tags = soup.find_all('a')
test_hrefs = []
for tag in test_tags:
    txt = tag.string
    if txt is not None and txt.startswith('Sold on'):
        test_hrefs.append(tag['href'])
test_hrefs[:3]

# Each one of these entries contains a 'class' and a 'href' attribute. What we are after is the href tag, which gives us the suffix of the specific property's webpage link. To extract that attribute, very simply do the following:

# To get the full link, we just need to append the suffix to the root URL, https://www.realestate.com.au. 

# Now that we have all the property links to the first page, we need to replicate the same process for the 2nd, 3rd, 4th etc. pages in the RealEstate website (just for NSW there are 55000 homes).
#
# FOr example the below snippet is the html corresponding to the 'Next' button (we can see it is just 'list-2', 'list-3' etc, so perhaps we could even just hardcode this in):
#
# ```HTML
# <a href="/buy/property-house-in-nsw/list-2?includeSurrounding=false" class="rui-button-brand pagination__link-next" title="Go to Next Page" rel="next"><span class="pagination__next-label">Next</span><span class="rui-icon rui-icon-forward-small"></span></a>
# ```
#
# Again, we can use BeautifulSoup's find_all method to look for 'a' tags can the class "rui-button-brand pagination__link-next".

# We actually don't need to use Selenium to scrape realestate.com.au, since its mostly a static html webpage. I can even just loop through the page numbers (ie. list-1,list-2,list-3...). Instead of Selenium I will use the python requests library to get the website.
#
# Below is the same snippet fom above that extracts the desired html tags from the site.
#
# Note: must specify user-agent***

page_hrefs = [
    f'/property/qld/north-lakes-4509?bedsMin=5&soldHistory=false&rentedHistory=true&types=House&sort=dateSoldNewest&page={i}'
    for i in range(1,11)
]
page_hrefs[-3:]

# Get links to each house's webpage
area_url = '/property/qld/north-lakes-4509/'
house_hrefs = []
for href in page_hrefs:
    browser.get(f'{onthehouse_url}{href}')
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    house_tags = soup.find_all('a')
    for tag in house_tags:
        href = tag.get('href')
        if href is not None and href.startswith(area_url):
            house_hrefs.append(href)
    sleep(np.random.lognormal(0,1))
house_links = list(set(house_hrefs))
df_house_hrefs = pd.DataFrame({'house_href': house_links})
df_house_hrefs.to_csv('/home/sma/dev/jnb/house_hrefs.csv')
house_links[:3]

len(set(house_hrefs))

soup.find('a').get('href')

# ### Scraping Code
#
# We need a some code to better handle retries in the web scrape since errors can happen at any point. The code ideally should also be able to retain the list obtained so far and save the page number and postcode that the web crawler is up to.

# +
# This code comes from: https://www.peterbe.com/plog/best-practice-with-retries-with-requests
# Basically we 'replace requests.get(...)', with 'requests_retry_session().get(...)'
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# -

# ## get house sold price and rent price

def get_price_date(url):
    browser.get(url)
    soup = BeautifulSoup(browser.page_source, 'html.parser')

    # Find the sold price div
    sold_price_div = soup.find('div', class_='xlText bold600 PropertyHistory__salePrice--sNxkh')
    if sold_price_div is None:
        sold_price = None
        sold_date = None
    else:
        sold_price = sold_price_div.text.strip().replace('$','').replace(',','') #780
        # Find the sold date div
        sold_date_div = sold_price_div.find_next_sibling('div', class_='text-secondary')
        sold_date = None if sold_date_div is None else datetime.strptime(sold_date_div.text.strip(),'%d %b %Y').date() #01 Nov 2022

    # Find the rent price div
    rent_price_div = soup.find('div', class_='xlText bold600 PropertyHistory__rentPrice--b9D1U')
    if rent_price_div is None:
        rent_price = None
        rent_date = None
    else:
        rent_price = rent_price_div.text.strip().replace('$','').replace('/w','') #780
        # Find the rent date div
        rent_date_div = rent_price_div.find_next_sibling('div', class_='text-secondary')
        rent_date = None if rent_date_div is None else datetime.strptime(rent_date_div.text.strip(),'%d %b %Y').date() #01 Nov 2022

    ret = [sold_price, sold_date, rent_price, rent_date, url.rsplit('/',1)[-1].replace('-',' ')]
    print(ret)
    return ret


data = []
for i, link in enumerate(house_links):
    try:
        dat = get_price_date(f'{onthehouse_url}{link}')
        if dat[0] is not None:
            data.append(dat)
        sleep(np.random.lognormal(0.1,1))
    except Exception as ex:
        print(f'{i}/{len(house_links)-1}: err')
        break
    finally:
        print(f'{i}/{len(house_links)-1}: {dat}')

df = pd.DataFrame(data, columns=['sold_price', 'sold_date', 'rent_price', 'rent_date', 'house_address'])
d1 = df.replace({'rent_price': {'1.00k': 1000}})
d2 = d1.dropna(subset=['rent_date'])
d2.shape

d3 = d2.sort_values(by='rent_date', ascending=False)
d3.head()
d3.to_csv('/home/sma/dev/jnb/house_rents.csv')

house_links = list(set(house_hrefs))
# req = requests_retry_session().get(f'{onthehouse_url}{house_links[1]}', headers=headers)
# soup = BeautifulSoup(req.content, 'html.parser')
browser.get(f'{onthehouse_url}{house_links[0]}')
soup = BeautifulSoup(browser.page_source, 'html.parser')

f'{onthehouse_url}{house_links[0]}'.rsplit('/',1)[-1].replace('-',' ')

# +
# Find the sold price div
sold_price_div = soup.find('div', class_='xlText bold600 PropertyHistory__salePrice--sNxkh')
if sold_price_div is None:
    sold_price = None
    sold_date = None
else:
    sold_price = sold_price_div.text.strip().replace('$','').replace(',','') #780
    # Find the sold date div
    sold_date_div = sold_price_div.find_next_sibling('div', class_='text-secondary')
    sold_date = None if sold_date_div is None else datetime.strptime(sold_date_div.text.strip(),'%d %b %Y').date() #01 Nov 2022

print(f'{sold_price} {sold_date}')

# Find the rent price div
rent_price_div = soup.find('div', class_='xlText bold600 PropertyHistory__rentPrice--b9D1U')
if rent_price_div is None:
    rent_price = None
    rent_date = None
else:
    rent_price = rent_price_div.text.strip().replace('$','').replace('/w','') #780
    # Find the rent date div
    rent_date_div = rent_price_div.find_next_sibling('div', class_='text-secondary')
    rent_date = None if rent_date_div is None else datetime.strptime(rent_date_div.text.strip(),'%d %b %Y').date() #01 Nov 2022

print(f'{rent_price} {rent_date}')
# -

req.content

# +
<span class="lgText text-left PropertyInfo__propertyDisplayPrice--7k6yF">Sold on 06 Jun 2023 for $775,000</span>
<div class="xlText bold600 PropertyHistory__rentPrice--b9D1U">$540/w</div>

<div class="xlText bold600 PropertyHistory__salePrice--sNxkh">$815,000</div>
<div class="text-secondary">22 Dec 2021</div>
<div class="xlText bold600 PropertyHistory__rentPrice--b9D1U">$780/w</div>
<div class="text-secondary">01 Nov 2022</div>

<div class="text-secondary">04 Dec 2021</div>
<div class="bold600 mdText">Sold for $1,190,000</div>
<div class="xlText bold600 PropertyHistory__rentPrice--b9D1U">$700/w</div>
<div class="text-secondary">04 Dec 2021</div>
# -

# One thing to make sure is the crawler doesn't try to go beyond the last page. If it does, it either starts looking at surrounding suburbs, or just displays a blank page. We can use the number of results summary at the top of the list (eg. '25 of 48 results') to calculate the maximum number of pages to visit.

req_test  = requests_retry_session().get( 'https://www.realestate.com.au/buy/in-pyrmont/list-1?includeSurrounding=false' ,headers=headers)
soup = BeautifulSoup(req_test.content, 'html.parser')
html_section = soup.find("div", class_="results-set-header__summary")
print(html_section.text)
print(re.findall(r"(\d+) result", html_section.text)[0])


def get_max_pages(url,useragent):
    headers = {'User-Agent': str(useragent)}
    req  = requests_retry_session().get( url + '1?includeSurrounding=false' ,headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    results = soup.find("div", class_="results-set-header__summary")
    num_results = re.findall(r"(\d+) result", results.text)[0]
    max_pages = ceil(int(num_results)/25)
    return max_pages


# Realestate.com.au does not display all 55000 homes when I filter by NSW, it limits the number of listed pages to 80. Therefore, it only shows up to 2000 homes, which is not a large enough dataset for us. One thing we can do is get a full NSW postcode list and do a search for each postcode (most likely no postcodes have more than 2000 ads). I found a postcode list that's been generously made public by Matthew Proctor here: https://www.matthewproctor.com/australian_postcodes
#
# After testing manually, looks like when you search by postcode the website becomes: 
#
# URL = 'https://www.realestate.com.au/buy/in' + POSTCODE + '/list-' + PAGE_NUMBER
#
# Below is code to loop through loop through each postcode and then extract each link.

# Get Postcodes
postcodes = pd.read_csv("./data/australian_postcodes.csv")
postcode_list=postcodes[postcodes.type=="Delivery Area"].postcode
nsw_postcodes = postcode_list[(postcode_list>=2000) & (postcode_list<=2999)].unique()
nsw_postcodes[:20]

# ### Get All Property Links
# For each postcode, get the max number of pages from the results count, and then loop through to get all the property links. 

# +
nsw_property_links = []
num_requests = 0
start_time = time()
i=0
headers={'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"}


for postcode in nsw_postcodes:
    url = 'https://www.realestate.com.au/buy/in-' + str(postcode) + '/list-'
    max_pages = get_max_pages(url, headers=headers) # get the number of pages of results
    num_requests += 1
    print('Postcode: '+ str(postcode) + ', Total pages: ' + str(max_pages))

    if max_pages == 0: # if there are 0 results, skip to the next postcode
        continue

    sleep(np.random.lognormal(0.3,1))

    nsw_property_links.extend(get_property_links(url, max_pages,headers)) # get all property links from each page, and add to end of list
    num_requests += max_pages
    elapsed_time = time() - start_time
    print('Request: {}; Frequency: {} requests/s'.format(num_requests, num_requests/elapsed_time))

    i+=1
    if i>=5:
        clear_output(wait=True)
        i=0

# -

# Yay! Looks like we have all 57k property links downloaded without errors! Now we can save the list of links using pickle

import pickle
# with open("./data/nsw_property_links.txt", "wb") as fp:   #Pickling
#     pickle.dump(nsw_property_links, fp)

# +
import pickle

with open("./data/nsw_property_links.txt", "rb") as fp:   # Unpickling
    nsw_property_links = pickle.load(fp)


# -

# ### Get Property Data Using Only Listing Pages
# Let's try to get as much property data as possible from the listing pages, since that's only 2200 requests as opposed to the 55000 requests if we extract from each individual property's web page.

# +
# Functions to extract features from Listing Pages (each page with approx 25 properties)
def get_link(soup):
    try:
        link = 'https://www.realestate.com.au' +  soup.find("a", class_="details-link residential-card__details-link")["href"]
        return link
    except:
        return "None"

def get_address(soup):
    try:
        address = soup.find("h2", class_="residential-card__address-heading").text
        return address
    except:
        return "None"

def get_price(soup):
    try:
        price =  soup.find("span", class_="property-price").text
        return price
    except:
        return "None"

def get_beds(soup):
    try:
        beds = soup.find("span", class_="general-features__icon general-features__beds").text
        return beds
    except:
        return "None"

def get_baths(soup):
    try:
        baths = soup.find("span", class_="general-features__icon general-features__baths").text
        return baths
    except:
        return "None"

def get_cars(soup):
    try:
        cars = soup.find("span", class_="general-features__icon general-features__cars").text
        return cars
    except:
        return "None"

def get_property_area(soup):
    try:
        property_area = soup.find("span", class_="property-size__icon property-size__building").text
        return property_area
    except:
        return "None"

def get_land_area(soup):
    try:
        land_area = soup.find("span", class_="property-size__icon property-size__land").text
        return land_area
    except:
        return "None"

def get_property_type(soup):
    try:
        property_type = soup.find("span", class_="residential-card__property-type").text
        return property_type
    except:
        return "None"


# +
def get_html_data(url,useragent):
    headers={'User-Agent': str(useragent)}
    req  = requests_retry_session().get( url, headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    return soup

def get_property_data(url,postcode, max_pages,useragent):
    property_data = []

    for i in range(max_pages):

        soup = get_html_data(url + str(i+1) + '?includeSurrounding=false', useragent)

        all_listings_html = soup.find_all("div", {'class':'residential-card__content'})
        for listing in all_listings_html:
            link = get_link(listing)
            address = get_address(listing)
            price = get_price(listing)
            beds = get_beds(listing)
            baths = get_baths(listing)
            cars = get_cars(listing)
            property_area = get_property_area(listing)
            land_area = get_land_area(listing)
            property_type = get_property_type(listing)
            property_data.append([link,
                      address,
                      postcode,
                      price,
                      beds,
                      baths,
                      cars,
                      property_area,
                      land_area,
                      property_type])

        print('page'+str(i+1))
        sleep(np.random.lognormal(0,1))

    return property_data


# -

# Similar code to ###'Get All Property Links' above, but we will use the get_property_data function to get the other features which are listed on the listings pages.

# +
nsw_property_data = []
num_requests = 0
i=0
ua = UserAgent() # Get list of fake user agents

start_time = time()
for postcode in nsw_postcodes:
    url = 'https://www.realestate.com.au/buy/in-' + str(postcode) + '/list-'
    max_pages = get_max_pages(url, useragent=ua.random) # get the number of pages of results
    num_requests += 1
    print('Postcode: '+ str(postcode) + ', Total pages: ' + str(max_pages))

    if max_pages == 0: # if there are 0 results, skip to the next postcode
        continue

    sleep(np.random.lognormal(0,1))

    nsw_property_data.extend(get_property_data(url,postcode, max_pages, useragent=ua.random)) # get all property links from each page, and add to end of list
    num_requests += max_pages
    elapsed_time = time() - start_time
    print('Requests: {}; Frequency: {:.3f} requests/s'.format(num_requests, num_requests/elapsed_time))
    print('Total Properties: {}; Elapsed Time: {:.3f}'.format(len(nsw_property_data),elapsed_time))

    i+=1
    if i>=5:
        clear_output(wait=True)
        i=0

# -

len(nsw_property_data)

nsw_property_data[:10]

# Full property data features
import pickle
with open("./data/nsw_property_data_full.pickle", "wb") as fp:   #Pickling
    pickle.dump(nsw_property_data, fp)

# +
import time
file_name = "data/nsw_property_data_" + str(time.strftime("%Y-%m-%d")) + ".csv"

columns = ["link",
           "address",
           "postcode", # If I run this next time, I will include the postcode
           "price",
           "num_beds",
           "num_baths",
           "num_cars",
           "property_area",
           "land_area",
           "property_type"]

(pd.DataFrame(nsw_property_data, columns = columns).
    to_csv(file_name, index = False, encoding = "UTF-8"))

# -

# ### Get Individual Property Features

# In each individual webpage, now we have to extract the relevant features. Test out the tags to search for each property attribute below.

def get_html_data(url,useragent):
    headers={'User-Agent': str(useragent)}
    req  = requests_retry_session().get( url, headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    return soup


# Below is are functions to extract features from the individual web page. Note: the tags might be slightly different to the ones used to extract data from the listing pages

# +
def get_address(soup):
    try:
        address = soup.find("h1", class_="property-info-address").text
        return address
    except:
        return "None"

def get_price(soup):
    try:
        price =  soup.find("span", class_="property-price property-info__price").text
        return price
    except:
        return "None"

def get_beds(soup):
    try:
        beds = soup.find("span", class_="general-features__icon general-features__beds").text
        return beds
    except:
        return "None"

def get_baths(soup):
    try:
        baths = soup.find("span", class_="general-features__icon general-features__baths").text
        return baths
    except:
        return "None"

def get_cars(soup):
    try:
        cars = soup.find("span", class_="general-features__icon general-features__cars").text
        return cars
    except:
        return "None"

def get_property_area(soup):
    try:
        property_area = soup.find("span", class_="property-size__icon property-size__building").text
        return property_area
    except:
        return "None"

def get_land_area(soup):
    try:
        land_area = soup.find("span", class_="property-size__icon property-size__land").text
        return land_area
    except:
        return "None"

def get_description(soup):
    try:
        description = soup.find("article", class_="property-description").text
        return description
    except:
        return "None"

def get_property_features(soup):
    try:
        property_features = soup.find_all("div", class_="property-features__feature")

        feature_list = [feature.text for feature in property_features]

        return feature_list
    except:
        return "None"


# +
# Don't use free Proxies - can be risky since we don't know what malware and viruses are on there
# import requests
# from itertools import cycle
# import traceback

# with open('data/ProxyList.txt') as f:
#     text = f.readlines()

# proxies = [line.strip('\n') for line in text]

# proxy_pool = cycle(proxies)
# -

def get_property_data(nsw_property_links):
    property_data = []
    i=0
    num_requests=0

    # Get list of fake user agents
    ua = UserAgent()

    start_time = time()
    for url in nsw_property_links:
        try:
            soup = get_html_data(url,ua.random)
        except:
            print("URL doesn't work. Try next one")
            continue

        address = get_address(soup)
        price = get_price(soup)
        beds = get_beds(soup)
        baths = get_baths(soup)
        cars = get_cars(soup)
        property_area = get_property_area(soup)
        land_area = get_land_area(soup)
        description = get_description(soup)
        feature_list = get_property_features(soup)

        property_data.append([address,
                             price,
                             beds,
                             baths,
                             cars,
                             property_area,
                             land_area,
                             description,
                             feature_list])

        num_requests+=1

        sleep(np.random.lognormal(0.3,1)) # perhaps we don't need to sleep since using proxies is pretty slow already

        elapsed_time = time() - start_time
        print('Requests: {}; Elapsed Time: {:.3f}; Frequency: {:.3f} requests/s'.format(num_requests, elapsed_time, num_requests/elapsed_time))

        i+=1
        if i>=5:
            clear_output(wait=True)
            i=0

        if num_requests % 2000 == 0:
            with open("./data/nsw_property_data.pickle", "wb") as fp:   #Pickling
                pickle.dump(property_data, fp)

            print("overwrite pickle at request no.:", num_requests)

    return property_data


property_data_10k = get_property_data(nsw_property_links[:10000])

len(property_data_10k)

property_data

with open("./data/nsw_property_data.pickle", "wb") as fp:   #Pickling
            pickle.dump(property_data, fp)

with open("./data/nsw_property_data.pickle", "rb") as fp:   #Pickling
            property_data=pickle.load(fp)


