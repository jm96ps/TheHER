from django.template.loader import get_template
from django.template import TemplateSyntaxError

try:
    t = get_template('index.html')
    print('Template loaded OK:', t)
except TemplateSyntaxError as e:
    print('TemplateSyntaxError:', e)
    raise
except Exception as e:
    print('Other error:', type(e), e)
    raise
