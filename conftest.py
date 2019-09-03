import pytest


def pytest_addoption(parser):
    parser.addoption(
        '--quick', action='store_true', help='Use existing input files in tests/data'
    )
    parser.addoption(
        '--fulldb', action='store_true', help='Test the fully-built conceptnet database'
    )


# https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option
def pytest_configure(config):
    config.addinivalue_line("markers", "requires_full_build: test requires the actual database to be built")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--fulldb"):
        # mark all 'requires_full_build_' tests as skipped
        skip_full = pytest.mark.skip(reason="need --fulldb option to run")
        for item in items:
            if "requires_full_build" in item.keywords:
                item.add_marker(skip_full)
