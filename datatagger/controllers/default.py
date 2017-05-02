# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is a sample controller
# - index is the default action of any application
# - user is required for authentication and authorization
# - download is for downloading files uploaded in the db (does streaming)
# -------------------------------------------------------------------------

@auth.requires_login()
def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    if request.vars.msg:
        msg = T(request.vars.msg)
    else:
        msg = T("Greetings "+str(auth.user.first_name)+'!')
    response.flash = msg
    return dict(message=T('Welcome to Data Tagger!'))

@auth.requires_login()
def view_annot():
    if not request.vars.page:
        page = 1
    else:
        page = int(request.vars.page)

    start = (page-1)*10
    end = page*10

    annots = db((db.Images.id==db.Labels.img_id)).select(db.Images.ALL, db.Labels.ALL, orderby=db.Images.id, limitby=(start, end))
    output_table = {}
    for row in annots:
        if row['Images']['id'] not in output_table:
            output_table[row['Images']['id']] = {'img_id':row['Images']['id'], 'img_path':row['Images']['img_path'], 'img_name':row['Images']['img_name'], 'label':[row['Labels']['label']], 'annotator':[row['Labels']['entry_by']]}
        else:
            output_table[row['Images']['id']]['label'].append(row['Labels']['label'])
            output_table[row['Images']['id']]['annotator'].append(row['Labels']['entry_by'])

    return locals()

@auth.requires_login()
def annot_image():
    form = SQLFORM(db.Labels)
    if form.process(session=None, formname='annotate').accepted:
        session.flash = 'Image Annotation : Success'
        redirect(URL('default', 'annot_image'))
    elif form.errors:
        session.flash = 'Image Annotation : Failed : Check for errors'

    if request.vars.img_id:
        img_id = int(request.vars.img_id)
    else:
        img_id = -1
        all_imgs = [i['id'] for i in db(db.Images.id>0).select(db.Images.id)]
        user_imgs = [i['img_id'] for i in db(db.Labels.entry_by==auth.user_id).select(db.Labels.img_id)]
        for im_id in all_imgs:
            if im_id not in user_imgs:
                img_id = im_id
                break

    return locals()

@auth.requires_login()
def refresh_data():
    import os
    image_path = '/home/mohit/research/web2py/applications/datatagger/static/data/arabic'
    images = [im for im in os.listdir(image_path) if im.endswith('.jpg')]
    
    ctr = 0
    db_images = [i['img_name'] for i in db(db.Images.id>0).select()]
    for img in images:
        if img not in db_images:
            db.Images.insert(img_name=img, img_path=image_path.split('static')[-1])
            ctr += 1

    db.commit()
    redirect(URL('default','index', vars={'msg':'database updated : %s new images' % str(ctr)}))

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


