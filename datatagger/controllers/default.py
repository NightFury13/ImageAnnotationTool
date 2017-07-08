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
def add_admin():
    admins = [i['user_id'] for i in db(db.Admins.id>0).select()]
    if auth.user_id not in admins:
        session.flash = 'Unauthorized Access! Action will be reported.'
        redirect('default','index')

    users = [(i['id'], i['first_name']+' '+i['last_name']) for i in db(db.auth_user.id>0).select(db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name) if i['id'] not in admins]

    if request.vars.u_id:
        db.Admins.insert(user_id=int(request.vars.u_id))
        session.flash = 'New Admin Added'
        redirect(URL('default','add_admin'))
    return locals()

@auth.requires_login()
def del_admin():
    admins = [i['user_id'] for i in db(db.Admins.id>0).select()]
    if auth.user_id not in admins:
        session.flash = 'Unauthorized Access! Action will be reported.'
        redirect('default','index')

    u_id = int(request.vars.u_id)
    db(db.Admins.user_id==u_id).delete()
    db.commit()
    session.flash = 'Admin rights revoked!'
    redirect(URL('default','add_admin'))

@auth.requires_login()
def view_annot():
    admins = [i['user_id'] for i in db(db.Admins.id>0).select()]
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
            final_label = ''
            try:
                final_label = db(db.FinalLabels.img_id==row['Images']['id']).select()[0]['label']
            except:
                final_label = '--'
            output_table[row['Images']['id']] = {'img_id':row['Images']['id'], 'img_path':row['Images']['img_path'], 'img_name':row['Images']['img_name'], 'label':[row['Labels']['label']], 'annotator':[row['Labels']['entry_by']], 'final_label':final_label}
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
    total_images = db((db.Images.id>0)&(db.Images.data_id==data_id)).count(db.Images.id)
    total_pages = int(total_images/10)

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
def del_dataset():
    if not request.vars.d_id:
        session.flash = 'No Dataset selected'
        redirect(URL('default','add_dataset'))

    d_id = int(request.vars.d_id)
    db(db.Datasets.id==d_id).delete()
    db.commit()
    redirect(URL('default','add_dataset'))

@auth.requires_login()
def del_metaset():
    if not request.vars.m_id:
        session.flash = 'No Metaset selected'
        redirect(URL('default','add_metaset'))
    
    m_id = int(request.vars.m_id)
    db(db.MetaSets.id==m_id).delete()
    db.commit()
    redirect(URL('default','add_metaset'))

@auth.requires_login()
def add_metaset():
    form = SQLFORM(db.MetaSets)
    if form.process().accepted:
        import os
        setid = int(form.vars.id)
        setname = form.vars.set_name
        langdata_path = os.path.join(form.vars.set_path, 'cropped')
        langdata_folders = os.listdir(langdata_path)
        
        meta_size = 0
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
            meta_size += 1
        
        db(db.MetaSets.id==setid).update(set_size=meta_size)
        response.flash = msg 
    elif form.errors:
        response.flash = 'MetaSet creation : Failed : Check form for errors'

    metasets = db(db.MetaSets.id>0).select()
    for metaset in metasets:
        metaset['datasets'] = ' || '.join([i['data_name'] for i in db(db.Datasets.data_set==metaset['id']).select()])
           
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

    try:
        labfile = os.path.join(image_path, [labf for labf in os.listdir(image_path) if labf.endswith('.txt')][0])
        with open(labfile, 'r') as f:
            labels = [i.strip().split() for i in f.readlines()]
            for label in labels:
                imgid = db(db.Images.img_name==label[0]).select()[0]['id']
                db.Labels.insert(img_id=imgid, label=' '.join(label[1:]))
    except:
        pass

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

@auth.requires_login()
def update_script():
    if not request.vars.s_id:
        session.flash = 'Error : No script provided to update!'
        redirect(URL('default', 'add_script'))
    else:
        script = db.Scripts(int(request.vars.s_id))
        form = SQLFORM(db.Scripts, script)
        if form.process().accepted:
            session.flash = 'Script updated'
            redirect(URL('default', 'add_script'))
        elif form.errors:
            response.flash = 'Script updation failed'
        return locals()

@auth.requires_login()
def settle_conflict():
    try:
        dataset_id = int(request.vars.dataset_id)
        images = db(db.Images.data_id==dataset_id).select()
        for img in images:
            try:
                labels = [i['label'] for i in db(db.Labels.img_id==img['id']).select(db.Labels.label, orderby=~db.Labels.entry_at)]
                if 'bad' not in [i.strip() for i in labels]:
                    final_label = db(db.Labels.img_id==img['id']).select(db.Labels.label, orderby=~db.Labels.entry_at)[0]['label']
                else:
                    final_label = 'bad'
            except:
                final_label = '--'
            try:
                db(db.FinalLabels.img_id==img['id']).update(label=final_label)
            except:
                db.FinalLabels.insert(img_id=img['id'], label=final_label)
        session.flash = 'Conflicting Annotations Resolved'
    except:
        session.flash = 'Resolving conflicting annotations failed!'

    redirect(URL('default', 'view_annot?data_id='+str(dataset_id)))

@auth.requires_login()
def download_metaset():
    if not request.vars.meta_id:
        session.flash = 'No Meta-dataset selected for download'
        redirect(URL('default', 'add_metaset'))
    else:
        meta_id = int(request.vars.meta_id)
        meta_name = db(db.MetaSets.id==meta_id).select()[0]['set_name']
        datasets = db(db.Datasets.data_set==meta_id).select()
        content = {}
        for dataset in datasets:
            data_name, content = prepare_dataset(dataset['id'], content)
        zip_name = meta_name+'_annotations.zip'
        download_url = serialize_and_zip(zip_name, content)
        redirect(download_url)

@auth.requires_login()
def download_dataset():
    if not request.vars.data_id:
        session.flash = 'No dataset selected for download'
        redirect(URL('default', 'select_db?redirect=1'))
    else:
        data_id = int(request.vars.data_id)
        data_name, content = prepare_dataset(data_id)
        zip_name = data_name+'_annotations.zip'
        download_url = serialize_and_zip(zip_name, content)
        redirect(download_url)

@auth.requires_login()
def mohit_download():
    import os
    if not request.vars.data_id:
        session.flash = 'No dataset selected!'
        redirect(URL('default', 'select_db?redirect=1'))

    data_id = int(request.vars.data_id)
    dataset = db(db.Datasets.id==data_id).select()[0]
    root_path = dataset['data_path']
    images = [i for i in os.listdir(root_path) if i.endswith('.jpg')]
    imgs_data = db((db.Images.data_id==data_id)&(db.FinalLabels.img_id==db.Images.id)).select()
    with open(os.path.join(root_path, 'corrected_annotation.txt'), 'w') as f:
        for img_data in imgs_data:
            label = img_data['FinalLabels']['label']
            if 'bad' not in [i.lower() for i in label.split()]:
                f.write(img_data['Images']['img_name']+' '+label+'\n')

    response.flash = 'Annotation file written : '+root_path
    return locals()

@auth.requires_login()
def prepare_dataset(data_id, content=None):
    import os
    from PIL import Image

    if not content:
        content = {}
    
    dataset = db(db.Datasets.id==data_id).select()[0]
    root_path = dataset['data_path'].split('cropped')[0]
    root_folder = filter(None, root_path.split('/'))[-1]
    root_images = [i for i in os.listdir(root_path) if i.endswith('.jpg') or i.endswith('.jpeg') or i.endswith('.png')]
    imgs_data = db((db.Images.data_id==data_id)&(db.FinalLabels.img_id==db.Images.id)).select()
    for img_data in imgs_data:
        label = img_data['FinalLabels']['label']
        if 'bad' not in [i.lower() for i in label.split()]:
            img_name = img_data['Images']['img_name']
            root_img_name = img_name.split('_')[0]
            try:
                xmin, ymin, xmax, ymax = img_name.split('.')[0].split('_')[2:]
            except:
                session.flash = 'Image file names follow incorrect format. Cannot extract bounding-box coordinates'
                redirect(URL('default', 'view_annot?data_id='+str(data_id)))

            if root_img_name not in content:
                try:
                    r_im_name = [i_name for i_name in root_images if root_img_name+'.jpg'==i_name or root_img_name+'.png'==i_name or root_img_name+'.jpeg'==i_name][0] # This one also has the extension
                except:
                    redirect(URL('default', 'index', vars={'msg':'Invalid Image Format : '+root_img_name+'. Only jpg, jpeg and png are supported'}))
                root_im = Image.open(os.path.join(root_path, r_im_name))
                r_depth = 3
                if not root_im.mode=='RGB':
                    r_depth = 1
                r_width, r_height = root_im.size

                content[root_img_name] = {'name':r_im_name, 'depth':r_depth, 'width':r_width, 'height':r_height, 'crops':[{'label':label, 'xmin':xmin, 'ymin':ymin, 'xmax':xmax, 'ymax':ymax}]}
                content[root_img_name]['root_folder'] = root_folder
            else:
                content[root_img_name]['crops'].append({'label':label, 'xmin':xmin, 'ymin':ymin, 'xmax':xmax, 'ymax':ymax})
    # Remove duplicates
    for r_im_n in content:
        content[r_im_n]['crops'] = [dict(t) for t in set([tuple(d.items()) for d in content[r_im_n]['crops']])]

    if not content:
        session.flash = 'Conflicts in annotations not resolved for '+dataset['data_name']+'!'
        redirect(URL('default','view_annot?data_id='+str(data_id)))

    return dataset['data_name'], content
    
@auth.requires_login()
def serialize_and_zip(zip_name, content):
    import os
    import zipfile

    # Create zip archive.
    zip_name = '_'.join(zip_name.split())
    zip_path = os.path.join(request.folder, 'static/data/downloads', zip_name)
    zipf = zipfile.ZipFile(zip_path, mode='w', compression=zipfile.ZIP_DEFLATED)

    for im_name in content:
        root_im = content[im_name]
        print root_im
        xml_str = """<annotation>
<folder>%s</folder>
<filename>%s</filename>
<path>%s</path>
<source>
    <database>Unknown</database>
</source>
<size>
    <width>%s</width>
    <height>%s</height>
    <depth>%s</depth>
</size>
<segmented>0</segmented>""" % (root_im['root_folder'], im_name, root_im['name'], root_im['width'], root_im['height'], root_im['depth'])

        for crop in root_im['crops']:
            xml_str+="""
<object>
    <name>%s</name>
    <pose>Unspecified</pose>
    <truncated>0</truncated>
    <difficult>0</difficult>
    <bndbox>
        <xmin>%s</xmin>
        <ymin>%s</ymin>
        <xmax>%s</xmax>
        <ymax>%s</ymax>
    </bndbox>
</object>""" % (crop['label'], crop['xmin'], crop['ymin'], crop['xmax'], crop['ymax'])
        
        xml_str+='\n</annotation>'
        zipf.writestr(im_name+'.xml', xml_str)

    zipf.close()
    download_url = 'http://ocr.iiit.ac.in/tagger/datatagger/static/data/downloads/'+zip_name

    return download_url

@auth.requires_login()
def download_file(filename, content):
    import cStringIO
    f_stream = cStringIO.StringIO()
    f_stream.write('Test File\n')
    filename = 'temp.txt'

    file_header = 'attachment; filename='+filename
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = file_header
    return f_stream.getvalue()

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

# Hard fixes to the portal.
def fix_issues():
    m_ids = range(5,11)
    d_ids = range(21, 32)

    """
    for i in ids:
        path = db(db.Datasets.id==i).select()[0]['data_path']
        n_path = path.split('/')
        n_path[1] = 'home'
        n_path[2] = 'webocr'
        n_path[3] = 'urdu_ocr'
        n_path = '/'.join(n_path)

        db(db.Datasets.id==i).update(data_path=n_path)
    """
    """
    for i in m_ids:
        path = db(db.MetaSets.id==i).select()[0]['set_path']
        n_path = path.split('/')
        n_path[1] = 'home'
        n_path[2] = 'webocr'
        n_path[3] = 'urdu_ocr'
        n_path = '/'.join(n_path)

        db(db.MetaSets.id==i).update(set_path=n_path)
    """
    """
    for i in d_ids:
        imgs = db(db.Images.data_id==i).select()
        break
    """
    return locals()

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


