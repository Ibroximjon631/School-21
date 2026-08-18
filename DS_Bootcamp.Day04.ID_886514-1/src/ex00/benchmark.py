import timeit


def use_loop(emails):
    new_list = list()
    for email in emails:
        if email.endswith('@gmail.com'):
            new_list.append(email)
    return new_list


def use_list_comprehension(emails):
    new_list = [email for email in emails if email.endswith('@gmail.com')]
    return new_list


def main():
    emails = ['john@gmail.com', 'james@gmail.com', 'alice@yahoo.com',
              'anna@live.com', 'philipp@gmail.com'] * 5

    setup_code = f"""
from __main__ import use_loop, use_list_comprehension
emails = {emails}
"""

    code_to_measure = 'use_loop(emails)'
    time_for_loop = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=900000)

    code_to_measure = 'use_list_comprehension(emails)'
    time_for_list_comr = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=900000)

    if time_for_list_comr <= time_for_loop:
        print('it is better to use a list comprehension')
    else:
        print('it is better to use a loop')

    times = sorted([time_for_loop, time_for_list_comr])

    print(f'{times[0]} vs {times[1]}')


if __name__ == '__main__':
    main()
