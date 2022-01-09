import pytest
from src.dl import DL


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("S01E01-S02E01", ("0101", "0201")),
        ("S01-S02", ("0100", "0299")),
        ("S01E03", ("0103", "0103")),
        ("S01", ("0100", "0199")),
        ("s01e01-s02e01", ("0101", "0201")),
        ("s01-s02", ("0100", "0299")),
        ("s01e03", ("0103", "0103")),
        ("s01", ("0100", "0199")),
        ("all", ("0000", "9999")),
    ],
)
def test_get_sortkey_range(test_input, expected):
    dl = DL
    assert dl.get_sortkey_range(dl, test_input) == expected
