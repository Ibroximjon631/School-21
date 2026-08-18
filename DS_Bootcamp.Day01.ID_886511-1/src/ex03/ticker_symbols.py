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


def search():
    if len(sys.argv) != 2:
        return

    arg = sys.argv[1]


    company = arg.capitalize()
    if company in COMPANIES:
        code = COMPANIES[company]
        print(STOCKS[code])
        return

    ticker = arg.upper()
    if ticker in STOCKS:
        for name, code in COMPANIES.items():
            if code == ticker:
                print(f"{name} {STOCKS[ticker]}")
                return
        print("Unknown company")
        return

    if arg.isupper():
        print("Unknown ticker")
    else:
        print("Unknown company")


if __name__ == "__main__":
    search()
