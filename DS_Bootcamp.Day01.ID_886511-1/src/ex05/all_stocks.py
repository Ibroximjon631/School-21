import sys


def return_answer():
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

    flag = 0
    if len(sys.argv) == 2:
        arg_string = sys.argv[1]
        flag = 1
        if ',,' in arg_string:
            flag = 0

    if (flag):
        args = [arg.strip() for arg in arg_string.split(',')]
        if '' in args:
            flag = 0
        if flag:
            for arg in args:
                arg_for_comp = arg.capitalize()
                arg_for_stocks = arg.upper()
                if arg_for_comp not in COMPANIES and arg_for_stocks not in STOCKS:
                    print(f'{arg} is an unknown company or an unknown ticker symbol')
                if arg_for_comp in COMPANIES:
                    print(f'{arg_for_comp} stock price is {STOCKS[COMPANIES[arg_for_comp]]}')
                if arg_for_stocks in STOCKS:
                    for key, value in COMPANIES.items():
                        if value == arg_for_stocks:
                            comp_name = key
                    print(f'{arg_for_stocks} is a ticker symbol for {comp_name}')


if __name__ == '__main__':
    return_answer()
