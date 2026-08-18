import sys


def parse_arguments_and_code():
    if len(sys.argv) != 4:
        raise Exception('An incorrect number of arguments is given')
    mode = sys.argv[1]
    text = sys.argv[2]
    shift = int(sys.argv[3])

    if mode == 'encode':
        encode(text, shift)
    elif mode == 'decode':
        decode(text, shift)


def encode(text, shift):
    new_text = ''
    for char in text:
        code = ord(char)
        if 97 <= code <= 122:
            new_code = (code - 97 + shift) % 26 + 97
        elif 65 <= code <= 90:
            new_code = (code - 65 + shift) % 26 + 65
        elif char in ' ,.:@?!/#$%&-' or 48 <= code <= 57:
            new_code = code
        else:
            raise Exception('The script does not support your language yet')

        new_text += chr(new_code)

    print(new_text)


def decode(text, shift):
    new_text = ''
    for char in text:
        code = ord(char)
        if 97 <= code <= 122:
            new_code = (code - 97 - shift) % 26 + 97
        elif 65 <= code <= 90:
            new_code = (code - 65 - shift) % 26 + 65
        elif char in ' ,.:@?!/#$%&-' or 48 <= code <= 57:
            new_code = code
        else:
            raise Exception('The script does not support your language yet')

        new_text += chr(new_code)

    print(new_text)


if __name__ == '__main__':
    parse_arguments_and_code()