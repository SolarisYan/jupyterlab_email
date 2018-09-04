import base64
import pandas as pd
from IPython.display import HTML
from io import BytesIO


CUSTOM_TAG = 'jupyterlab_email_data'
EXCEL_ENGINE = 'xlsxwriter'


def attach(data, filename, type):
    if isinstance(data, pd.DataFrame) or \
       isinstance(data, pd.Series):
        if type == 'csv':
            data = data.to_csv()
        elif type == 'tsv':
            data = data.to_csv(sep='\t')
        elif type in ('xls', 'xlsx'):
            io = BytesIO()
            writer = pd.ExcelWriter(io, engine=EXCEL_ENGINE)
            data.to_excel(writer)
            writer.save()
            data = base64.b64encode(io.getvalue()).decode('ascii')
    if type not in ('csv', 'tsv',
                    'png', 'pdf',
                    'xls', 'xlsx',
                    'txt', 'html'):
        raise Exception('Attachment type not recognized %s' % type)

    if not filename.endswith('.' + type):
        filename = filename + '.' + type

    html = '<{tag} filename="{filename}" localdata="{data}">(Attachment: {filename})</{tag}>'.format(
        tag=CUSTOM_TAG, filename=filename, data=data)
    return HTML(html)