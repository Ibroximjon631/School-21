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


def use_map(emails):
    def check_gmail(email):
        if email.endswith('@gmail.com'):
            return email

    return map(check_gmail, emails)


def main():
    emails = ['john@gmail.com', 'james@gmail.com', 'alice@yahoo.com',
              'anna@live.com', 'philipp@gmail.com'] * 5

    setup_code = f"""
from __main__ import use_loop, use_list_comprehension, use_map
emails = {emails}
"""

    code_to_measure = 'use_loop(emails)'
    time_for_loop = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=900000)

    code_to_measure = 'use_list_comprehension(emails)'
    time_for_list_comr = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=900000)

    code_to_measure = 'use_map(emails)'
    time_for_map = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=900000)

    times = [time_for_loop, time_for_list_comr, time_for_map]
    sorted_times = sorted(times)
    min_time = sorted_times[0]

    if min_time == time_for_map:
        print('it is better to use a map')
    elif min_time == time_for_list_comr:
        print('it is better to use a list comprehension')
    else:
        print('it is better to use a loop')

    print(f'{sorted_times[0]} vs {sorted_times[1]} vs {sorted_times[2]}')


if __name__ == '__main__':
    main()
