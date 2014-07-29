import conceptnet5
import inspect
import os


def get_code_base():
    return os.path.dirname(inspect.getsourcefile(conceptnet5))


if __name__ == '__main__':
    print(get_code_base())
