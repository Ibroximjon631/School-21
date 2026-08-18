class Must_read():
    with open('data.csv') as file:
        data = file.read()
    print(data)

if __name__ == '__main__':
    Must_read()