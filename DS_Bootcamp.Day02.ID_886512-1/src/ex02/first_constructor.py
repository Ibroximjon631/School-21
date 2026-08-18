class Research():
    def file_reader(self):
        with open('data.csv') as file:
            data = file.read()
        return data


if __name__ == '__main__':
    object = Research()
    print(object.file_reader())
