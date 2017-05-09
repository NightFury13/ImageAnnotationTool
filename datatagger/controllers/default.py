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

    try:
        data_id = int(request.vars.data_id)
    except:
        redirect(URL('default','index', vars={'msg':'Something went wrong : Please select a Dataset before proceeding'}))

    annots = db((db.Images.id>0)&(db.Images.id==db.Labels.img_id)&(db.Images.data_id==data_id)).select(db.Images.ALL, db.Labels.ALL, orderby=db.Images.id, limitby=(start, end))
    output_table = {}
    for row in annots:
        if row['Images']['id'] not in output_table:
            output_table[row['Images']['id']] = {'img_id':row['Images']['id'], 'img_path':row['Images']['img_path'], 'img_name':row['Images']['img_name'], 'label':[row['Labels']['label']], 'annotator':[row['Labels']['entry_by']]}
        else:
            output_table[row['Images']['id']]['label'].append(row['Labels']['label'])
            output_table[row['Images']['id']]['annotator'].append(row['Labels']['entry_by'])

    return locals()

@auth.requires_login()
def select_db():
    redirect_fl = 0
    if not request.vars.redirect:
        redirect(URL('default','index', vars={'msg':'Something went wrong, please try again'}))

    datasets = db(db.Datasets.id>0).select()
    redirect_fl = int(request.vars.redirect)
   
    return locals() 

@auth.requires_login()
def annot_image():
    if not request.vars.page:
        page = 1
    else:
        page = int(request.vars.page)
    start = (page-1)*10
    end = page*10

    try:
        data_id = int(request.vars.data_id)
    except:
        redirect(URL('default','index', vars={'msg':'Something went wrong : Please select a Dataset before proceeding'}))

    img_ids = [i['id'] for i in db((db.Images.id>0)&(db.Images.data_id==data_id)).select(db.Images.id, orderby=db.Images.id, limitby=(start, end))]

    return locals()

@auth.requires_login()
def label_to_db():
    img_id = request.vars.current_id
    all_ids = request.vars.img_id
    idx = 0
    for im_id in all_ids:
        if im_id==img_id:
            break
        idx+=1
    label = request.vars.label[idx]
    img_id = int(img_id)
    try:
        if not db((db.Labels.img_id==img_id)&(db.Labels.entry_by==auth.user_id)).select():
            db.Labels.insert(label=label, img_id=img_id)
            return DIV('Image Annotation : Success : Label Added', _class="alert alert-success")
        else:
            db((db.Labels.img_id==img_id)&(db.Labels.entry_by==auth.user_id)).update(label=label)
            return DIV('Image Annotation : Success : Label Updated', _class="alert alert-success")
    except:
        return DIV('Image Annotation : Failed : Check for errors', _class="alert alert-danger")

@auth.requires_login()
def add_metaset():
    form = SQLFORM(db.MetaSets)
    if form.process().accepted:
        import os
        setid = int(form.vars.id)
        setname = form.vars.set_name
        langdata_path = os.path.join(form.vars.set_path, 'cropped')
        langdata_folders = os.listdir(langdata_path)
        
        msg = 'MetaSet Creation : Success : '
        for langdata_folder in langdata_folders:
            if not os.listdir(os.path.join(langdata_path, langdata_folder)):
                continue
            try:
                script = db(db.Scripts.script_name==langdata_folder).select()[0]['id']
            except:
                session.flash = 'Invalid MetaSet directory structure : Non-supported script : '+langdata_folder
                continue
            msg += langdata_folder+' : '
            data_id = db.Datasets.insert(data_name=setname+'~'+langdata_folder, data_path=os.path.join(langdata_path, langdata_folder), data_script=script, data_set=setid)
            db.commit()

            refresh_data(data_id)
        response.flash = msg 
    elif form.errors:
        response.flash = 'MetaSet creation : Failed : Check form for errors'
           
    return locals() 
        
@auth.requires_login()
def add_dataset():
    form = SQLFORM(db.Datasets)
    if form.process().accepted:
        data_id = form.vars.id
        name = form.vars.data_name
        path = form.vars.data_path
        refresh_data(data_id, name, path)
    elif form.errors:
        session.flash = 'New dataset addition : Failed : Check form for errors'

    datasets = db(db.Datasets.id>0).select()
    
    return locals()
        
@auth.requires_login()
def update_db():
    if not request.vars.data_id:
        redirect(URL('default','index', vars={'msg':'Dataset updation : Failed : Invalid Dataset-ID'}))
    data_id = int(request.vars.data_id)

    refresh_data(data_id)
    
    redirect(URL('default', 'add_dataset'))

@auth.requires_login()
def refresh_data(data_id, data_name=None, data_path=None):
    import os

    try:
        dataset = db(db.Datasets.id==data_id).select()[0]
        data_name = dataset['data_name']
        data_path = dataset['data_path']
    except:
        if not data_name or not data_path:
            redirect(URL('default','index', vars={'msg':'Dataset updation : Failed : Check form for errors'}))
        
    image_path = data_path
    images = []
    try:
        images = [im for im in os.listdir(image_path) if im.endswith('.jpg') or im.endswith('.png')]
    except:
        db(db.Datasets.id==data_id).delete()
        db.commit()
        redirect(URL('default','index', vars={'msg':'Dataset updation : Failed : No such path %s' % data_path}))
    
    ctr = 0
    db_images = [i['img_name'] for i in db((db.Images.id>0)&(db.Images.data_id==data_id)).select()]
    for img in images:
        if img not in db_images:
            db.Images.insert(img_name=img, img_path=image_path.split('static')[-1], data_id=data_id)
            ctr += 1

    prev_size = db(db.Datasets.id==data_id).select()[0]['data_size']
    db(db.Datasets.id==data_id).update(data_size=prev_size+ctr)
    db.commit()
    session.flash = 'Dataset updation : Success : %s : %s new images' % (data_name, str(ctr))

@auth.requires_login()
def add_script():
    form = SQLFORM(db.Scripts)
    if form.process().accepted:
        response.flash = 'Script Addition : Success'
    elif form.errors:
        response.flash = 'Script Addition : Failed : Check form for errors'

    scripts = db(db.Scripts.id>0).select()
    return locals()


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


