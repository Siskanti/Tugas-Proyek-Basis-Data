# Email dan Password Untuk Login
# user1 = admin1@gmail.com - 232323
# user2 = admin@gmail.com - 12345678

from urllib import request
from flask import Flask, render_template, session, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_mongoengine import MongoEngine
from flask_paginate import Pagination, get_page_parameter
import bcrypt

db = MongoEngine()
app = Flask(__name__)
bootstrap = Bootstrap5(app)

app.config['MONGODB_SETTINGS'] = {
    'host': 'mongodb://localhost/tugas_proyek'
}
app.config.update(dict(SECRET_KEY='yoursecretkey'))


@app.before_request
def before_request():
    session.modified = True


db.init_app(app)


class Kategori(db.Document):
    kategori = db.StringField()


class Tags(db.Document):
    tags = db.StringField()
    count = db.IntField(default=1)


class User(db.Document):
    nama = db.StringField()
    email = db.StringField()
    password = db.StringField()


class Dokumen(db.Document):
    judul = db.StringField(required=True)
    penulis = db.StringField(required=True)
    kategori = db.StringField(required=True)
    tanggal = db.DateField(required=True)
    isi = db.StringField(textarea=True)
    tags_split = db.StringField()
    hit = db.IntField(default=0)
    tags = db.ListField()


@app.route('/')
@app.route('/home')
def home():
    try:
        page = request.args.get('page')
        page = int(page)
    except:
        page = 1

    per_page = 5
    data2 = Dokumen.objects().order_by('-tanggal').paginate(page, per_page).items

    jdata = len(Dokumen.objects)
    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(
        prev_label='Back',
        next_label='Next',
        page=page,
        per_page=per_page,
        total=jdata,
        record_name='Berita',
        format_total=True,
        format_number=True,
        css_framework='bootstrap5')

    kategori = Kategori.objects()
    tags = Tags.objects().order_by('-count').limit(-10)
    favData = Dokumen.objects().order_by('-hit').limit(-5)

    return render_template('home.html', datas=data2, kategori=kategori, pagination=pagination, favData=favData, tags=tags)


@app.route("/login", methods=["POST", "GET"])
def login():
    kategori = Kategori.objects()
    tags = Tags.objects().order_by('-count').limit(-10)
    message = 'Please Login to Your Account'
    if "email" in session:
        return redirect(url_for('admin'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        email_found = User.objects(email=email).first()
        if email_found:
            email_val = email_found.email
            passwordcheck = email_found.password

            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck.encode('utf-8')):
                session["email"] = email_val
                return redirect(url_for('admin'))
            else:
                if "email" in session:
                    return redirect(url_for("admin"))
                message = 'Wrong Password'
                return render_template('login.html', message=message, kategori=kategori, tags=tags)
        else:
            message = 'Email Not Found'
            return render_template('login.html', message=message, kategori=kategori, tags=tags)
    return render_template('login.html', message=message, kategori=kategori, tags=tags)


@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/admin')
def admin():
    if "email" in session:
        try:
            page = request.args.get('page')
            page = int(page)
        except:
            page = 1

        per_page = 5
        data = Dokumen.objects().order_by('-tanggal').paginate(page, per_page).items

        jdata = len(Dokumen.objects)
        page = request.args.get(get_page_parameter(), type=int, default=1)
        pagination = Pagination(
            prev_label='Back',
            next_label='Next',
            page=page,
            per_page=per_page,
            total=jdata,
            record_name='Berita',
            format_total=True,
            format_number=True,
            css_framework='bootstrap5')

        kategori = Kategori.objects()
        tags = Tags.objects().order_by('-count').limit(-10)
        return render_template('devAdmin.html', data=data, kategori=kategori, pagination=pagination, tags=tags)
    else:
        return redirect(url_for('home'))


@app.route('/detail/<id>')
def detail(id):
    data = Dokumen.objects(id=id).first()
    Dokumen.objects(id=id).modify(upsert=True, new=True, inc__hit=1)
    kategori = Kategori.objects()
    tags = Tags.objects().order_by('-count').limit(-10)
    return render_template('detail.html', data=data, kategori=kategori, id=id, tags=tags)


@app.route('/detail-admin/<id>')
def detail2(id):
    if "email" in session:
        data = Dokumen.objects(id=id).first()
        kategori = Kategori.objects()
        tags = Tags.objects().order_by('-count').limit(-10)
        return render_template('detailAdmin.html', data=data, kategori=kategori, id=id, tags=tags)
    else:
        return redirect(url_for('home'))


@app.route('/form-data', methods=['POST', 'GET'])
def formdata():
    if "email" in session:
        if request.method == "POST":
            judul = request.form.get("judul")
            penulis = request.form.get("penulis")
            tanggal = request.form.get("tanggal")
            isi = request.form.get("isi")
            kategori = request.form.get("kategori").title()
            tags_split = request.form.get("tags").title()
            tag = tags_split.title().split(',')[:5]
            for a in range (len(tag)):
                tag[a] = tag[a].lstrip().rstrip()

            user_input = {
                'judul': judul,
                'penulis': penulis,
                'tanggal': tanggal,
                'isi': isi,
                'kategori': kategori,
                'tags_split': ', '.join([str(item) for item in tag]),
                'tags': tag}

            Dokumen(**user_input).save()

            for a in range(len(tag)):
                if Tags.objects(tags__exact=tag[a]):
                    Tags.objects(tags=tag[a]).modify(upsert=True, new=True, inc__count=1)
                else:
                    Tags(tags=tag[a]).save()

            if Kategori.objects(kategori__exact=kategori):
                return redirect(url_for('admin'))
            else:
                Kategori(kategori=kategori).save()
                return redirect(url_for('admin'))
        else:
            kategori = Kategori.objects()
            tags = Tags.objects().order_by('-count').limit(-10)
            return render_template('form.html', kategori=kategori, tags=tags)
    else:
        return redirect(url_for('home'))


@app.route('/form-edit/<id>', methods=['POST', 'GET'])
def formedit(id):
    if "email" in session:
        data = Dokumen.objects(id=id).first()
        old_tags = data.tags

        if request.method == "POST":
            judul = request.form.get("judul")
            penulis = request.form.get("penulis")
            tanggal = request.form.get("tanggal")
            isi = request.form.get("isi")
            kategori = request.form.get("kategori").title()
            tags_split = request.form.get("tags").title()
            tag = tags_split.title().split(',')[:5]
            for a in range (len(tag)):
                tag[a] = tag[a].lstrip().rstrip()

            user_input = {
                'judul': judul,
                'penulis': penulis,
                'tanggal': tanggal,
                'isi': isi,
                'kategori': kategori,
                'tags_split': ', '.join([str(item) for item in tag]),
                'tags': tag}

            Dokumen.objects(id=id).update(**user_input)

            for a in range(len(old_tags)):
                if Tags.objects(tags__exact=old_tags[a]):
                    Tags.objects(tags=old_tags[a]).modify(upsert=True, new=True, dec__count=1)
                    if Tags.objects(count__lt=1):
                        Tags.objects(tags=old_tags[a]).delete()

            for a in range(len(tag)):
                if Tags.objects(tags__exact=tag[a]):
                    Tags.objects(tags=tag[a]).modify(upsert=True, new=True, inc__count=1)
                else:
                    Tags(tags=tag[a]).save()

            if not (Dokumen.objects(kategori=data.kategori)):
                Kategori.objects(kategori=data.kategori).delete()

            if Kategori.objects(kategori__exact=kategori):
                return redirect(url_for('admin'))
            else:
                Kategori(kategori=kategori).save()
                return redirect(url_for('admin'))
                
        else:
            kategori = Kategori.objects()
            tags = Tags.objects().order_by('-count').limit(-10)
            return render_template('formedit.html', data=data, id=id, kategori=kategori, tags=tags)
    else:
        return redirect(url_for('home'))


@app.route('/hapus-berita/<id>')
def hapusberita(id):
    if "email" in session:
        data = Dokumen.objects(id=id).first()
        old_tags = data.tags
        for a in range(len(old_tags)):
            if Tags.objects(tags__exact=old_tags[a]):
                Tags.objects(tags=old_tags[a]).modify(upsert=True, new=True, dec__count=1)
                if Tags.objects(count__lt=1):
                    Tags.objects(tags=old_tags[a]).delete()
        
        Dokumen.objects(id=id).delete()

        if not (Dokumen.objects(kategori=data.kategori)):
            Kategori.objects(kategori=data.kategori).delete()

        return redirect(url_for('admin'))
    else:
        return redirect(url_for('home'))


@app.route('/<who>/list-berita')
def listberita(who):
    if (who == "home"):
        data = Dokumen.objects()
        kategori = Kategori.objects()
        tags = Tags.objects().order_by('-count').limit(-10)
        return render_template('listBerita.html', kategori=kategori, data=data, tags=tags, who=who)
    else:
        if "email" in session:
            data = Dokumen.objects()
            kategori = Kategori.objects()
            tags = Tags.objects().order_by('-count').limit(-10)
            return render_template('listBerita.html', kategori=kategori, data=data, tags=tags, who=who)
        else:
            return redirect(url_for('home'))


@app.route('/<who>/list-berita/<orderBy>')
def orderBy(orderBy, who):
    try:
        page = request.args.get('page')
        page = int(page)
    except:
        page = 1

    per_page = 5
    if (orderBy == "Terbaru"):
        data = Dokumen.objects().order_by('-tanggal').paginate(page, per_page).items
        judul = "Terbaru"
        jdata = len(Dokumen.objects())
    elif (orderBy == "Terlama"):
        data = Dokumen.objects().order_by('tanggal').paginate(page, per_page).items
        judul = "Terlama"
        jdata = len(Dokumen.objects())
    else:
        if Kategori.objects(kategori__exact=orderBy):
            data = Dokumen.objects(kategori=orderBy).order_by('-tanggal').paginate(page, per_page).items
            judul = orderBy
            jdata = len(Dokumen.objects(kategori=orderBy))
        else:
            data = Dokumen.objects(tags=orderBy).order_by('-tanggal').paginate(page, per_page).items
            judul = orderBy
            jdata = len(Dokumen.objects(tags=orderBy))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(
        prev_label='Back',
        next_label='Next',
        page=page,
        per_page=per_page,
        total=jdata,
        record_name='Berita',
        format_total=True,
        format_number=True,
        css_framework='bootstrap5')

    kategori = Kategori.objects()
    tags = Tags.objects().order_by('-count').limit(-10)
    if (who == "home"):
        return render_template('orderBy.html', kategori=kategori, data=data, pagination=pagination, judul=judul, tags=tags)
    else:
        if "email" in session:
            return render_template('AdminOrderBy.html', kategori=kategori, data=data, pagination=pagination, judul=judul, tags=tags)
        else:
            return redirect(url_for('home'))


if __name__ == '__main__':
    app.run()
