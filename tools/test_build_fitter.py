from webapp.services.fitting_service import build_fitter_from_request

form={'delimiter':',','current_col':'1','potential_col':'2'}
with open('test_fixture.csv','rb') as f:
    files={'datafile': f}
    fitter=build_fitter_from_request(form, files)
    print('Fitter created:', type(fitter))
    print('file_path:', fitter.file_path)
    print('parsed:', getattr(fitter,'_parsed',None))
    print('raw shape:', None if fitter._raw is None else fitter._raw.shape)
    print('delimiter used:', getattr(fitter,'delimiter',None))
