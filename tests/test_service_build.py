import os
from webapp.services import fitting_service


def test_build_fitter_from_sample():
    sample = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'sample.csv')
    form = {'file_path': os.path.abspath(sample)}
    fitter = fitting_service.build_fitter_from_request(form, files=None)
    # Expect a hydrogen_fitting instance (has attribute 'fit_data')
    assert hasattr(fitter, 'fit_data')
    assert hasattr(fitter, 'potential') or hasattr(fitter, '_raw')


def test_run_fit_separates_internal_log_variables():
    fixture = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'test_fixture.csv')
    form = {
        'file_path': os.path.abspath(fixture),
        'current_col': '1',
        'potential_col': '2',
        'area_electrode': '1.0',
        'model_type': 'simplified',
        'n_starts': '1',
        'vary_k1': 'true',
        'vary_bbv': 'false',
    }
    res = fitting_service.run_fit(form)
    assert res['success'] is True

    # Physical parameters must NOT contain internal log variables
    params = res['parameters']
    assert 'k1' in params
    assert 'k1r' in params
    assert 'k2' in params
    assert 'k2r' in params
    assert 'bbv' in params
    assert 'bbh' in params
    for k in params:
        assert not k.startswith('log_'), f"Unexpected internal parameter in parameters: {k}"

    # Internal parameters dictionary contains the log variables
    internal = res['internal_parameters']
    assert 'log_k1' in internal
    assert 'log_k1r' in internal
    assert 'log_k2' in internal
    assert 'log_k2r' in internal

    # Physical parameters must be marked as Fitted when they were fitted
    details = res['parameters_details']
    assert details['k1']['vary'] is True
    assert details['k1']['status'] == 'Fitted'
    assert details['bbv']['vary'] is False
    assert details['bbv']['status'] == 'Fixed'


def test_run_fit_full_model_marks_derived_rates():
    fixture = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'test_fixture.csv')
    form = {
        'file_path': os.path.abspath(fixture),
        'current_col': '1',
        'potential_col': '2',
        'area_electrode': '1.0',
        'model_type': 'full',
        'n_starts': '1',
        'vary_k1': 'false',
    }
    res = fitting_service.run_fit(form)
    assert res['success'] is True

    details = res['parameters_details']
    # k1 was explicitly fixed
    assert details['k1']['vary'] is False
    assert details['k1']['status'] == 'Fixed'

    # k2r and k3r are thermodynamically derived in full model
    assert details['k2r']['status'] == 'Derived'
    assert details['k2r']['vary'] is False
    assert details['k3r']['status'] == 'Derived'
    assert details['k3r']['vary'] is False


def test_get_params_dict_internal_flag():
    from webapp.models.hydrogen import HydrogenFitting
    fixture = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'test_fixture.csv')
    fitter = HydrogenFitting(file_path=fixture, area_electrode=1.0)
    fitter.fit_data(model_type='simplified', n_starts=1)

    p_default = fitter.get_params_dict()
    assert 'k1' in p_default
    for k in p_default:
        assert not k.startswith('log_')

    p_internal = fitter.get_params_dict(include_internal=True)
    assert 'log_k1' in p_internal
    assert 'k1' in p_internal


def test_run_fit_volmer_tafel():
    fixture = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'test_fixture.csv')
    form = {
        'file_path': os.path.abspath(fixture),
        'current_col': '1',
        'potential_col': '2',
        'area_electrode': '1.0',
        'model_type': 'Volmer-Tafel',
        'n_starts': '1',
        'vary_k1': 'true',
        'vary_k3': 'true',
        'vary_k3r': 'true',
    }
    res = fitting_service.run_fit(form)
    assert res['success'] is True
    params = res['parameters']
    assert 'k1' in params
    assert 'k1r' in params
    assert 'k3' in params
    assert 'k3r' in params
    assert 'bbv' in params
    assert 'k2' not in params
    assert 'bbh' not in params
    details = res['parameters_details']
    assert details['k3']['status'] == 'Fitted'
    assert details['k3r']['status'] == 'Fitted'


