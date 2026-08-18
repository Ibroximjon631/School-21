def data_types():
    a = 42
    b = "hello"
    c = 3.14
    d = True
    e = [1, 2, 3]
    f = {"key": "value"}
    g = (1, 2, 3)
    h = {1, 2, 3}

    types_list = [type(x).__name__ for x in (a, b, c, d, e, f, g, h)]
    print(types_list)


if __name__ == '__main__':
    data_types()
