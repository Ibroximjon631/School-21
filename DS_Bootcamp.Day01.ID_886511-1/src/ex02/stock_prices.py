import sys

COMPANIES = {
    'Apple': 'AAPL',
    'Microsoft': 'MSFT',
    'Netflix': 'NFLX',
    'Tesla': 'TSLA',
    'Nokia': 'NOK'
}

STOCKS = {
    'AAPL': 287.73,
    'MSFT': 173.79,
    'NFLX': 416.90,
    'TSLA': 724.88,
    'NOK': 3.37
}


def search_price():
    if len(sys.argv) != 2:
        return

    company = sys.argv[1].capitalize()

    if company in COMPANIES:
        code = COMPANIES[company]
        print(STOCKS[code])
    else:
        print("Unknown company")


if __name__ == "__main__":
    search_price()
