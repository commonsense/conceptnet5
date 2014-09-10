from assoc_space import AssocSpace


def run():
    ENTRIES = [
        (4, '/c/en/apple', '/c/en/red'),
        (1, '/c/en/apple', '/c/en/green'),
        (3, '/c/en/apple', '/c/en/orange'),
        (3, '/c/en/banana', '/c/en/orange'),
        (1, '/c/en/banana', '/c/en/yellow'),
        (0.5, '/c/en/lemon', '/c/en/yellow'),
        (1.5, '/c/en/orange', '/c/en/lemon'),
        (0.1, '/c/en/apple', '/c/en/lemon'),
        (0.2, '/c/en/banana', '/c/en/lemon'),
        (0.5, '/c/en/ideas', '/c/en/colorless'),
        (0.5, '/c/en/ideas', '/c/en/green'),
        (1, '/c/en/example', '/c/en/green'),
    ]
    space = AssocSpace.from_entries(ENTRIES, k=4)
    space.save_dir('../conceptnet5/support_data/testdata/input/assoc_space')

if __name__ == '__main__':
    run()
