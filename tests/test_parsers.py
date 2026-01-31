import os
from webapp.utils.parsers import parse_data_file


def test_parse_sample():
    sample = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'sample.csv')
    pot, cur = parse_data_file(sample, delimiter=',', current_col=1, potential_col=2)
    assert len(pot) > 0
    assert len(cur) > 0
    assert pot.shape == cur.shape
