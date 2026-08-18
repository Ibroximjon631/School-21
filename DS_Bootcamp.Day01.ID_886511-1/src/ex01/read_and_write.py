def open_file():
    with open('ds.csv') as file:
        data = file.readlines()
    return data


def parse_lines(data):
    new_arr = []
    for line in data:
        new_line = ''
        flag = False
        for char in line:
            if char == '"':
                flag = not flag
            if char == "," and not flag:
                new_line += '\t'
            else:
                new_line += char
        new_arr.append(new_line)
    return new_arr


def create_and_write_in_file(new_lines):
    with open('ds.tsv', 'w') as file:
        file.writelines(new_lines)


if __name__ == '__main__':
    data = open_file()
    new_lines = parse_lines(data)
    create_and_write_in_file(new_lines)
