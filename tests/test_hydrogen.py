import os
import numpy as np
from webapp.models.hydrogen import hydrogen_fitting

FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'test_fixture.csv')

def test_parse_and_fit():
    f = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0, ohmic_drop=0.0,
                         current_col=1, potential_col=2, delimiter='auto', current_units='A',
                         bbv_initial=0.5, bbh_initial=0.5)
    assert f._parsed is True
    res = f.fit_data(model_type='full', fitting_method='powell')
    assert f.result_model is not None
    params = f.get_params_dict()
    assert 'k1' in params and isinstance(params['k1'], float)

def test_theta_and_tafel():
    f = hydrogen_fitting(file_path=FIXTURE, area_electrode=1.0, ohmic_drop=0.0,
                         current_col=1, potential_col=2, delimiter='auto', current_units='A',
                         bbv_initial=0.5, bbh_initial=0.5)
    f.fit_data(model_type='full', fitting_method='powell')
    theta = f.compute_theta()
    assert theta.shape == np.asarray(f.potential).shape
    x, slope = f.compute_tafel_slope()
    assert x.shape == slope.shape
