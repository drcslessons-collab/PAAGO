import numpy as np
from paago_repro.core import paired_signflip_exact, parse_seed


def test_parse_seed():
    assert parse_seed("v63_exp7_paago_valf2_seed27182/results.csv") == 27182


def test_signflip_identical_is_one():
    a = np.array([1., 2., 3.])
    assert paired_signflip_exact(a, a) == 1.0

