import conceptnet_web
import inspect
import os


def get_package_dir():
    return os.path.dirname(inspect.getsourcefile(conceptnet_web))


def get_code_base():
    return os.path.dirname(get_package_dir())


if __name__ == '__main__':
    print(get_code_base())
