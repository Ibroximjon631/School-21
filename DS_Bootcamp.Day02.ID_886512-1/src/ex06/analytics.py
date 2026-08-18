import sys
from random import randint
import logging
import requests

logging.basicConfig(
    filename='analytics.log',
    level=logging.DEBUG,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class Research():
    def __init__(self):
        self.filepath = sys.argv[1]
        self.telegram_token = '7823021591:AAEw18u8Mr8tim2Mw31h8lilawg87W4-k-E'
        self.chat_id = '450396489'
        logging.info('Initialized Research with filepath: %s', self.filepath)

    def check_file(self):
        lines = self.lines
        flag = 1
        if len(lines[0].split(',')) != 2:
            flag = 0
            logging.warning('The first line does not have two columns.')
        for i in range(1, len(lines)):
            if sum(list(map(int, lines[i].split(',')))) != 1:
                flag = 0
                logging.warning('Line %d does not contain 0 and 1: %s', i, lines[i])

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
                logging.info('File read successfully with %d entries.', len(new_list))
                return new_list
            else:
                logging.error('The file structure is incorrect.')
                raise Exception('The file has a different structure, and program cannot read it')

    def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logging.info('Telegram message sent successfully: %s', message)
        else:
            logging.error('Failed to send message to Telegram: %s', response.text)

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
            logging.info('Calculated counts: heads=%d, tails=%d', object.heads, object.tails)
            return object.heads, object.tails

        @staticmethod
        def fractions(object):
            total = object.heads + object.tails
            heads_prob = object.heads / total * 100
            tails_prob = object.tails / total * 100
            logging.info('Calculated fractions: heads_prob=%.2f, tails_prob=%.2f', heads_prob, tails_prob)
            return heads_prob, tails_prob

    class Analytics(Calculations):
        def predict_random(num_of_preds=3):
            pred_list = []
            heads_pred = tails_pred = 0
            for _ in range(num_of_preds):
                first = randint(0, 1)
                second = 0 if first == 1 else 1
                pred_list.append([first, second])
            for l in pred_list:
                if l[0] == 1:
                    heads_pred += 1
                if l[1] == 1:
                    tails_pred += 1
            logging.info('Predicted random results: heads_pred=%d, tails_pred=%d', heads_pred, tails_pred)
            return heads_pred, tails_pred

        @staticmethod
        def predict_last(object):
            mylist = object.file_reader()
            logging.info('Last prediction: %s', mylist[-1])
            print(mylist[-1] if mylist else [])

        @staticmethod
        def save_file(data, filename, extension):
            with open(f'{filename}.{extension}', 'w') as file:
                file.write(data)
                logging.info('Data saved to %s.%s', filename, extension)
