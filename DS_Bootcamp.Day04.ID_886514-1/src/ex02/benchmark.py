import timeit
import sys


def use_loop(emails):
    new_list = list()
    for email in emails:
        if email.endswith('@gmail.com'):
            new_list.append(email)
    return new_list


def use_list_comprehension(emails):
    new_list = [email for email in emails if email.endswith('@gmail.com')]
    return new_list


def use_map(emails):
    def check_gmail(email):
        if email.endswith('@gmail.com'):
            return email

    return map(check_gmail, emails)


def use_filter(emails):
    def check_gmail(email):
        return email if email.endswith('@gmail.com') else None

    new_list = filter(lambda x: x is not None, map(check_gmail, emails))
    return new_list


def main():
    emails = ['john@gmail.com', 'james@gmail.com', 'alice@yahoo.com',
              'anna@live.com', 'philipp@gmail.com'] * 5

    setup_code = f"""
from __main__ import use_loop, use_list_comprehension, use_map, use_filter
emails = {emails}
"""
    mode = sys.argv[1]
    num_of_calls = int(sys.argv[2])

    if mode == 'loop':
        code_to_measure = 'use_loop(emails)'
        time_for_loop = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=num_of_calls)
        print(time_for_loop)
    elif mode == 'list_comprehension':
        code_to_measure = 'use_list_comprehension(emails)'
        time_for_list_comr = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=num_of_calls)
        print(time_for_list_comr)
    elif mode == 'map':
        code_to_measure = 'use_map(emails)'
        time_for_map = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=num_of_calls)
        print(time_for_map)
    elif mode == 'filter':
        code_to_measure = 'use_filter(emails)'
        time_for_filter = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=num_of_calls)
        print(time_for_filter)


if __name__ == '__main__':
    main()