__version__ = '0.0.7'

from .nbconvert import run as run_nbconvert
from ._email import email as email_notebook
from .attachments import attach


def _jupyter_server_extension_paths():
    return [{
        "module": "jupyterlab_email.extension"
    }]
