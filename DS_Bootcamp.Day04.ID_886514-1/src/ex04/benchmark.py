import timeit
import random
from collections import Counter


def my_function(my_list):
    my_dict = dict()
    for item in my_list:
        if item not in my_dict:
            my_dict[item] = 0
        my_dict[item] += 1
    return my_dict


def use_counter(my_list):
    c = Counter(my_list)
    return c


def my_top(my_list):
    my_dict = my_function(my_list)
    sorted_items = sorted(my_dict.items(), key=lambda item: item[1], reverse=True)
    return dict(sorted_items[:10])


def counter_top(my_list):
    c = Counter(my_list)
    return c.most_common(10)


def main():
    my_list = [random.randint(0, 100) for _ in range(100000)]

    setup_code = f"""
from __main__ import my_function, use_counter, my_top, counter_top
my_list = {my_list}
"""
    code_to_measure = 'my_function(my_list)'
    time = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=1)
    print(f'my function: {time}')

    code_to_measure = 'use_counter(my_list)'
    time = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=1)
    print(f'Counter: {time}')

    code_to_measure = 'my_top(my_list)'
    time = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=1)
    print(f'my top: {time}')

    code_to_measure = 'counter_top(my_list)'
    time = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=1)
    print(f'Counter\'s top: {time}')


if __name__ == '__main__':
    main()
