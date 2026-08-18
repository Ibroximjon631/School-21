def create_new_dict():
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

    result = dict()

    for curr_tuple in list_of_tuples:
        key = curr_tuple[1]
        value = curr_tuple[0]
        if key not in result:
            result[key] = []
        result[key].append(value)

    return result


def print_dict(mydict):
    for key, value in mydict.items():
        for values in value:
            print(f"'{key}' : '{values}'")


if __name__ == '__main__':
    mydict = create_new_dict()
    print_dict(mydict)
