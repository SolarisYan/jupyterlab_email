import json
import emails
import base64
import nbformat
from bs4 import BeautifulSoup
from six import iteritems
from .nbconvert import run
from .attachments import CUSTOM_TAG


def make_email(path, model, from_, type='email', template='', code=False, subject='',
               also_attach='none', also_attach_pdf_template='', also_attach_html_template=''):
    '''
        path        : path to notebook
        model       : notebook itself (in case deployment strips outputs or
                      notebook not available except through ContentsManager)
        from_       : address to send the email from
        type        : type to convert notebook to
        template    : template to use when converting notebook
        code        : include input cells in notebook
        subject     : subject of email
        also_attach : also attach pdf/html/both
    '''
    name = path.rsplit('/', 1)[1].rsplit('.', 1)[0]
    model = nbformat.writes(nbformat.reads(json.dumps(model), 4))

    if type == 'email':
        type_to = 'html'
    elif type == 'html attachment':
        type_to = 'html'
    elif type == 'pdf attachment':
        type_to = 'pdf'
    else:
        raise Exception('Type not recognized')

    nb = run(type_to, name, model, template)

    if also_attach in ('pdf', 'both'):
        pdf_nb = run('pdf', name, model, also_attach_pdf_template)
    if also_attach in ('html', 'both'):
        html_nb = run('html', name, model, also_attach_html_template)

    if not nb:
        raise Exception('Something went wrong with NBConvert')

    if type == 'email':
        soup = BeautifulSoup(nb, 'html.parser')

        # strip markdown links
        for item in soup.findAll('a', {'class': 'anchor-link'}):
            item.decompose()

        # strip matplotlib base outs
        for item in soup.find_all('div', class_='output_text output_subarea output_execute_result'):
            for c in item.contents:
                if '&lt;matplotlib' in str(c):
                    item.decompose()

        # remove dataframe table borders
        for item in soup.findAll('table', {'border': 1}):
            item['border'] = 0
            item['cellspacing'] = 0
            item['cellpadding'] = 0

        # extract imgs for outlook
        imgs = soup.find_all('img')
        imgs_to_attach = {}

        # attach main part
        for i, img in enumerate(imgs):
            if not img.get('localdata'):
                continue
            imgs_to_attach[img.get('cell_id') + '_' + str(i) + '.png'] = base64.b64decode(img.get('localdata'))
            img['src'] = 'cid:' + img.get('cell_id') + '_' + str(i) + '.png'
            # encoders.encode_base64(part)
            del img['localdata']

        attaches = soup.find_all(CUSTOM_TAG)
        att_to_attach = {}
        # attach custom attachments
        for i, att in enumerate(attaches):
            if not att.get('localdata'):
                continue
            filename = att.get('filename')
            if filename.endswith('.png') or \
               filename.endswith('.xls') or \
               filename.endswith('.xlsx') or \
               filename.endswith('.pdf'):
                att_to_attach[filename] = base64.b64decode(att.get('localdata'))
            else:
                att_to_attach[filename] = att.get('localdata')
            att.decompose()

        # assemble email soup
        soup = str(soup)
        message = emails.html(charset='utf-8', subject=subject, html=soup, mail_from=from_)

        for img, data in iteritems(imgs_to_attach):
            message.attach(filename=img, content_disposition="inline", data=data)

        for att, data in iteritems(att_to_attach):
            message.attach(filename=att, content_disposition="inline", data=data)

        if also_attach in ('pdf', 'both'):
            message.attach(filename=name + '.pdf', data=pdf_nb)

        if also_attach in ('html', 'both'):
            message.attach(filename=name + '.html', data=html_nb)
        return message
    message = emails.html(subject=subject, html='<html>Attachmend: %s.%s</html>' % (name, type_to), mail_from=from_)
    message.attach(filename=name + '.' + type_to, data=nb)

    if also_attach in ('pdf', 'both'):
        message.attach(filename=name + '.pdf', data=pdf_nb)

    if also_attach in ('html', 'both'):
        message.attach(filename=name + '.html', data=html_nb)

    return message


def email(message, to, username, password, domain, host, port):
    '''
        to          : who to send notebook to
        username    : email account username
        password    : email account password
        domain      : email account provider
        host        : smtp host
        port        : smtp port
    '''
    r = message.send(to=to,
                     smtp={'host': host,
                           'port': port,
                           'ssl': True,
                           'user': username,
                           'password': password})
    if r.status_code != 250:
        print(r)
        raise Exception('Email exception! Check username and password')
    return r
