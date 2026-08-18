import sys
import resource
import time

def read_file():
    file_path = sys.argv[1]
    with open(file_path, 'r') as file:
        for line in file:
            yield line

if __name__ == '__main__':
    start_time = time.time()
    lines = read_file()
    for line in lines:
        pass
    end_time = time.time()
    peak_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)
    print(f"Peak Memory Usage = {peak_memory:.3f} GB")
    print(f"User Mode Time + System Mode Time = {end_time - start_time:.2f}s")