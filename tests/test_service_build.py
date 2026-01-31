import os
from webapp.services import fitting_service


def test_build_fitter_from_sample():
    sample = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'sample.csv')
    form = {'file_path': os.path.abspath(sample)}
    fitter = fitting_service.build_fitter_from_request(form, files=None)
    # Expect a hydrogen_fitting instance (has attribute 'fit_data')
    assert hasattr(fitter, 'fit_data')
    assert hasattr(fitter, 'potential') or hasattr(fitter, '_raw')
