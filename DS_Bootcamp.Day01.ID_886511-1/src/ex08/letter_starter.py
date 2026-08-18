import sys


def write_letter():
    lines = open_file()
    email = input('Please enter email: ')
    name = search_name(lines, email)
    print(
        f'Dear {name}, welcome to our team. We are sure that it will be a pleasure to work with you. That’s a precondition for the professionals that our company hires.')


def open_file():
    file_path = './employees.tsv'
    with open(file_path) as file:
        data = file.readlines()
    return data


def search_name(lines, email):
    mydict = dict()
    for line in lines:
        line = line.strip()
        mydict[line.split('\t')[2]] = line.split('\t')[0]
    return mydict[email]


if __name__ == '__main__':
    write_letter()
