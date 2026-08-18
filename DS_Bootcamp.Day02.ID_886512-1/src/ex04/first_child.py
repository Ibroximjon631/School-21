import sys
from random import randint


class Research():
    def __init__(self):
        self.filepath = sys.argv[1]

    def check_file(self):
        lines = self.lines
        flag = 1
        if len(lines[0].split(',')) != 2:
            flag = 0
        for i in range(1, len(lines)):
            if sum(list(map(int, lines[i].split(',')))) != 1:
                flag = 0

        return flag

    def file_reader(self, has_header=True):
        with open(self.filepath) as file:
            self.lines = file.readlines()
            flag = self.check_file()
            if flag:
                new_list = []
                if has_header:
                    start = 1
                else:
                    start = 0
                for i in range(start, len(self.lines)):
                    new_list.append(list(map(int, self.lines[i].split(','))))
                return new_list
            else:
                raise Exception('The file has a different structure, and program cannot read it')

    class Calculations():
        @staticmethod
        def counts(object):
            mylist = object.file_reader()
            object.heads = object.tails = 0
            for items in mylist:
                if items[0] == 1:
                    object.heads += 1
                if items[1] == 1:
                    object.tails += 1
            print(object.heads, object.tails)

        @staticmethod
        def fractions(object):
            total = object.heads + object.tails
            print(object.heads / total * 100, object.tails / total * 100)

    class Analytics(Calculations):
        def predict_random(num_of_preds=3):
            pred_list = []
            for _ in range(num_of_preds):
                first = randint(0, 1)
                second = 0 if first == 1 else 1
                pred_list.append([first, second])
            print(pred_list)

        @staticmethod
        def predict_last(object):
            mylist = object.file_reader()
            print(mylist[-1] if mylist else [])


if __name__ == '__main__':
    object = Research()
    print(object.file_reader())
    Research.Calculations.counts(object)
    Research.Calculations.fractions(object)
    Research.Analytics.predict_random()
    Research.Analytics.predict_last(object)
