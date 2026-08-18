import requests
from bs4 import BeautifulSoup
import sys
import time
import re


def get_args():
    ticker = sys.argv[1]
    field = sys.argv[2]
    return ticker, field


def get_response(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception('URL does not exist')
    return response


def parse_html(response, field):
    soup = BeautifulSoup(response.text, 'html.parser')

    rows = soup.find_all('div', {'class': re.compile('row lv-0')})
    if not rows:
        raise Exception('Unable to find a table for a ticker')

    for row in rows:
        label = row.find('div', {'class': re.compile('rowTitle')})
        if label and label.text.strip() == field:
            values = row.find_all('div', {'class': re.compile('column yf-')})
            values_txt = [value.text.strip() for value in values]
            return (values_txt)

    raise Exception('The requested field does not exist')


if __name__ == '__main__':
    try:
        ticker, field = get_args()
        url = f'https://finance.yahoo.com/quote/{ticker}/financials'
        response = get_response(url)
        values = parse_html(response, field)
        time.sleep(5)
        print((field, *values))
    except Exception as e:
        print(e)
