import timeit
import sys
from functools import reduce

def use_loop(num):
    sum = 0
    for i in range(1, num + 1):
        sum += i * i
    return sum

def use_reduce(num):
    return reduce(lambda sum, x: sum + x * x, range(1, num + 1))

def main():
    mode = sys.argv[1]
    num_of_calls = int(sys.argv[2])
    num = int(sys.argv[3])

    setup_code = f"""
from __main__ import use_loop, use_reduce
num = {num}
"""
    if mode == 'loop':
        code_to_measure = 'use_loop(num)'
        time_for_loop = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=num_of_calls)
        print(time_for_loop)

    if mode == 'reduce':
        code_to_measure = 'use_reduce(num)'
        time_for_reduce = timeit.timeit(stmt=code_to_measure, setup=setup_code, number=num_of_calls)
        print(time_for_reduce)

if __name__ == '__main__':
    main()