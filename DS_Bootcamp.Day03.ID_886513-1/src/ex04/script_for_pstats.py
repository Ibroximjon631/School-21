import pstats
import cProfile
import financial_enhanced
import asyncio
import sys


def sort_and_save_profile(file_name, output_file, top_n=5):
    # Создаем объект Stats из файла профилирования
    p = pstats.Stats(file_name)

    # Сортируем по накопленному времени
    p.sort_stats('cumulative')

    # Сохраняем топ N в новый файл
    with open(output_file, "w") as f:
        p.stream = f
        p.print_stats(top_n)


if __name__ == "__main__":
    ticker = sys.argv[1]
    field = sys.argv[2]
    cProfile.run(f'asyncio.run(financial_enhanced.main())', 'profiling-http.prof')
    sort_and_save_profile("profiling-http.prof", "pstats-cumulative.txt")