import os
import re
import json
import requests
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from bs4 import BeautifulSoup


def main():
    # url = 'https://www.carsales.com.au/cars/details/2008-toyota-kluger-kx-r-auto-2wd/SSE-AD-12654588'
    # dd = get_car_detail(url)

    model = 'Corolla'
    has_data = False

    if not has_data:
        get_car_data(model)

    # process
    d1 = pd.read_csv(f'{model}_Dealer_detail.csv')
    d2 = pd.read_csv(f'{model}_Private_detail.csv')
    df = (
        pd.concat([d1, d2])
        .astype({'year': int, 'odokm': float, 'price': int})
        .fillna(0)
        .query('year >= 2010 and year < 2020 and odokm <= 150000')
        .sort_values('odokm', ascending=False)
    )

    cur_year = pd.Timestamp.now().year
    if model == 'Kluger':
        grades = []
        drives = []
        for name in df.name:
            lname = name.lower()
            grade = (
                3
                if 'grande' in lname
                else (2 if ('kx-s' in lname or 'gxl' in lname) else 1)
            )
            drive = 'AWD' if 'awd' in lname else '2WD'
            grades.append(grade)
            drives.append(drive)
        df['grade'] = grades
        df['drive'] = drives
        df = df.assign(
            age=lambda x: x.year - cur_year,
            year=lambda x: x.year
            + (x.grade - 2) * 0.3
            + np.where(x.drive == '2WD', 0, 0.12),
        )
    elif model == 'Corolla':
        grades = []
        drives = []
        for name in df.name:
            lname = name.lower()
            grade = 3 if 'zr' in lname else (2 if 'sx' in lname else 1)
            drive = 'hybrid' if 'hybrid' in lname else 'fuel'
            grades.append(grade)
            drives.append(drive)
        df['grade'] = grades
        df['drive'] = drives
        df = df.assign(
            age=lambda x: x.year - cur_year,
            year=lambda x: x.year
            + (x.grade - 2) * 0.3
            + np.where(x.drive == 'fuel', 0, 0.12),
        )
    bins = [0, 50000, 75000, 100000, 125000, 150000, np.inf]
    lbls = ['050k', '075k', '100k', '125k', '150k', 'maxk']
    sybs = ['circle', 'triangle-up', 'square', 'diamond', 'cross', 'x']
    syb_map = dict(zip(lbls, sybs))
    df['lvlkm'] = pd.cut(
        df['odokm'], bins=bins, labels=lbls, right=True, include_lowest=True
    )
    df['price'] *= 0.0001
    df['odokm'] *= 0.0001
    fig = px.scatter(
        df,
        x='year',
        y='price',
        color='owner',
        symbol='lvlkm',
        symbol_map=syb_map,
        custom_data=['name', 'odokm', 'color', 'price_guide', 'price_change'],
    )
    fig.update_layout(legend_traceorder="reversed")
    fig.update_traces(
        hovertemplate='%{customdata[0]} <br>%{customdata[1]:.2f}km %{customdata[2]} <br>$%{y:.2f} <br>%{customdata[3]} <br>%{customdata[4]}'
    )
    fig.update_layout(
        xaxis=dict(
            tickmode='linear',
            tick0=2010,
            dtick=1.0,
        )
    )
    fig.show()
    ok = 1


def get_car_data(model: str):
    for seller in ['Private', 'Dealer']:
        # get basic info
        file = f'{model}_{seller}_info'
        num, df = get_car_info(seller, model)
        dfs = [df]
        cnt = df.shape[0]
        while cnt < num:
            _, df = get_car_info(seller, model, offset=cnt)
            dfs.append(df)
            cnt += df.shape[0]
        df = pd.concat(dfs, axis=0, ignore_index=True).assign(
            date=pd.Timestamp.now().normalize()
        )
        df.to_csv(f'{file}.csv', index=False)
        # append
        file = f'{file}_all.csv'
        if not os.path.isfile(file):
            d1 = df
        else:
            d0 = pd.read_csv(file).drop_duplicates()
            d1 = pd.concat([d0, df], axis=0, ignore_index=True)
        d1.to_csv(file, index=False)

        # get details
        file = f'{model}_{seller}_detail'
        dat = []
        for url in df.url:
            cols, vals = get_car_detail(url)
            dat.append(vals)
        dd = pd.DataFrame(dat, columns=cols)
        df = pd.concat([df, dd], axis=1).get(
            [
                'id',
                'owner',
                'name',
                'year',
                'odokm',
                'price',
                'color',
                'post_code',
                'registration',
                'price_guide',
                'price_change',
                'last_price_date',
                'last_price_value',
                'last_modified',
                'date',
                'url',
            ]
        )
        df.to_csv(f'{file}.csv', index=False)
        # append
        file = f'{file}_all.csv'
        if not os.path.isfile(file):
            d1 = df
        else:
            d0 = pd.read_csv(file)
            d1 = pd.concat([d0, df], axis=0, ignore_index=True)
        d1.to_csv(file, index=False)


def get_car_info(seller: str, model: str, offset: int = 0) -> pd.DataFrame:
    offset_term = '' if offset == 0 else f'&offset={offset}'
    # url = f'https://www.carsales.com.au/cars/toyota/{model}/queensland-state/?sort=%7eYear{offset_term}'
    url = (
        get_search_url(
            seller=seller, model=model, year=(2011, 2020), odometer=(None, 150000)
        )
        + offset_term
    )
    page_text = get_page_text(url)

    # parse html
    soup = BeautifulSoup(page_text, 'html.parser')
    rset = soup.find("script", type="application/ld+json")  # find_all return a list
    js = json.loads(rset.string)['mainEntity']
    num = js['numberOfItems']
    data = []
    for elem in js['itemListElement']:
        item = elem['item']
        url = item['url']
        name = item['name']
        print(name)
        year = name[:4]
        odokm = item['mileageFromOdometer']['value']
        id = f'{year}-' + url.rsplit('/', 2)[-2]

        price = item['offers']['price']
        images = item['image']
        owner = (
            'private'
            if (len(images) == 0 or 'private' in images[0]['url'])
            else 'dealer'
        )
        data.append((id, name, year, odokm, price, owner, url))
    columns = ['id', 'name', 'year', 'odokm', 'price', 'owner', 'url']
    df = pd.DataFrame.from_records(data, columns=columns)

    return num, df


def get_car_detail(url: str) -> pd.DataFrame:
    print(f'===> Car detail url: {url}')
    page_text = get_page_text(url)
    # with open('page.txt', 'w') as f:
    #     f.write(page_text)

    # with open('page.txt', 'r') as f:
    #     page_text = f.read()

    # parse html
    soup = BeautifulSoup(page_text, 'html.parser')

    # color
    item = soup.find(class_='col features-item-value features-item-value-colour')
    if item is None:
        color = 'None'
    else:
        color = item.text.strip()

    # last modified
    item = soup.find(class_='col features-item-value features-item-value-last-modified')
    if item is None:
        last_modified = 'None'
    else:
        last_modified = pd.to_datetime(item.text.strip(), dayfirst=True)

    # registration
    item = soup.find(
        class_='col features-item-value features-item-value-registration-expiry'
    )
    if item is None:
        registration = 'None'
    else:
        registration = item.text.strip()

    # post_code, price_range, price_guide, price_change
    post_code = ''
    rmin = ''
    rmax = ''
    price_change_count = 1
    price_change_amount = 0
    price_change_events = ''
    last_price_date = ''
    last_price_value = ''
    pmin = ''
    pmax = ''
    dmin = ''
    dmax = ''
    for r in soup.find_all('script'):
        rtext = r.text
        if 'window.Csn.PageData.advertTags = ' in rtext:
            for txt in rtext.split(';'):
                if 'window.Csn.PageData.advertTags = ' in txt:
                    js = json.loads(txt.split('=')[1])['tags']
                    post_code = js['pcode']
                    rmin = str_num(js['price_range'])[:-1]
                    rmax = str_num(js['price'])
        elif 'var price_insights_data = ' in rtext:
            txt = rtext.strip()[len('var price_insights_data = ') : -1]
            js = json.loads(txt)['priceInsights']
            # price change hisory
            try:
                price_hist = js['priceChangeHistory']['content']
                price_change_count = price_hist['totalPriceChanges']
                price_change_amount = int(price_hist['totalPriceChangeAmount'])
                price_change_events_ = price_hist['priceChangeEvents']
                for price_event in price_change_events_:
                    date = pd.Timestamp(price_event['eventDateTimeUtc']).strftime(
                        '%Y-%m-%d'
                    )
                    price = str_num(price_event['price'])
                    price_change_events += f'{date}:{price};'
                    last_price_date = date
                    last_price_value = price
                if len(price_change_events) > 0:
                    price_change_events = price_change_events[:-1]
            except Exception as exc:
                print(exc)
                pass
            # estimatedPriceGuide
            try:
                price_guide_ = js['estimatedPriceGuide']['content']
                price_private = price_guide_['privateVehicle']
                price_dealer = price_guide_['dealerVehicle']
                pmin = str_num(price_private["min"])
                pmax = str_num(price_private["max"])
                dmin = str_num(price_dealer["min"])
                dmax = str_num(price_dealer["max"])
            except Exception as exc:
                print(exc)
                pass
    price_guide = f'{rmin}({pmin}.{dmin})-{rmax}({pmax}.{dmax})'
    price_change = f'cnt:{price_change_count}-amt:{price_change_amount}-evts:[{price_change_events}]'

    cols = (
        'last_price_date',
        'last_price_value',
        'color',
        'registration',
        'post_code',
        'last_modified',
        'price_guide',
        'price_change',
    )
    vals = (
        last_price_date,
        last_price_value,
        color,
        registration,
        post_code,
        last_modified,
        price_guide,
        price_change,
    )

    return cols, vals


def get_page_text(url: str) -> str:
    # if pretend as web browser, carsales will reject
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;",
        "Accept-Encoding": "gzip",
        "Referer": "http://www.example.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    }
    res = requests.get(url, headers=headers)
    page_text = res.text
    return page_text


def get_search_url(
    make: str = 'Toyota',
    model: str = 'Kluger',
    seller: str = 'Private',
    year: tuple = (2011, 2019),
    odometer: tuple = (None, 150000),
) -> str:
    url = (
        'https://www.carsales.com.au/cars/?q=(And.Service.CARSALES._.(C.State.Queensland._.Region.Brisbane.)'
        f'_.Year.range({year[0]}..{year[1]})._.Odometer.range({odometer[0]}..{odometer[1]})._.GenericGearType.Automatic.'
        f'_.SellerType.{seller}._.AdsWith.Photos._.AdsWith.Prices._.(C.Make.{make}._.Model.{model}.))'
    )
    return url


def str_num(txt):
    val = re.findall(r'\d+', str(txt))
    if len(val) == 0:
        return ''
    else:
        return val[0]


if __name__ == '__main__':
    main()
    ok = 1
