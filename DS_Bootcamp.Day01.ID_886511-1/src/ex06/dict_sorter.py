def create_dict(list_of_tuples):
    mydict = {}
    for curr in list_of_tuples:
        key = int(curr[1])
        value = curr[0]
        if key not in mydict:
            mydict[key] = []
        mydict[key].append(value)
    mydict = dict(sorted(mydict.items(), reverse=True))
    return mydict


def sort_countries(countries_dict):
    for value in countries_dict.values():
        value = sorted(value)
        print(*value, sep='\n')


def display_countries():
    list_of_tuples = [
        ('Russia', '25'),
        ('France', '132'),
        ('Germany', '132'),
        ('Spain', '178'),
        ('Italy', '162'),
        ('Portugal', '17'),
        ('Finland', '3'),
        ('Hungary', '2'),
        ('The Netherlands', '28'),
        ('The USA', '610'),
        ('The United Kingdom', '95'),
        ('China', '83'),
        ('Iran', '76'),
        ('Turkey', '65'),
        ('Belgium', '34'),
        ('Canada', '28'),
        ('Switzerland', '26'),
        ('Brazil', '25'),
        ('Austria', '14'),
        ('Israel', '12')
    ]

    countries_dict = create_dict(list_of_tuples)
    sort_countries(countries_dict)


if __name__ == '__main__':
    display_countries()

