from flask import Flask,render_template,request,session,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import json
from datetime import datetime
import os
import math

with open("templates/config.json", "r") as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.secret_key = params['secret_key']
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = params['sender_email']
app.config['MAIL_PASSWORD'] = params['sender_passwd']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_url']
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/databaseblog'
#app.config['SQLALCHEMY_DATABSE_URI']='mysql://{user}:{password}@{server}/{database}'.format(user='root', password='', server='localhost', database='databaseblog')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
if not os.path.exists('db.sqlite'):
    db.create_all()


class Contacts(db.Model):
   sno = db.Column(db.Integer, primary_key = True, autoincrement=True)
   name = db.Column(db.String(100), unique = False)
   email = db.Column(db.String(50))  
   phone_num = db.Column(db.String(15))
   msg = db.Column(db.String(200))
   date = db.Column(db.DateTime, default=datetime.utcnow)

class Messages(db.Model):
   sno = db.Column(db.Integer, primary_key = True, autoincrement=True)
   name = db.Column(db.String(100), unique = False)
   message = db.Column(db.String(200))
   date = db.Column(db.DateTime, default=datetime.utcnow)

class Posts(db.Model):
   sno = db.Column(db.Integer, primary_key = True, autoincrement=True)
   title = db.Column(db.String(100), unique = False)
   slug = db.Column(db.String(50))  
   content = db.Column(db.String(200))
   tagline = db.Column(db.String(200))
   img_file = db.Column(db.String(25))
   date = db.Column(db.DateTime, default=datetime.utcnow)
   

@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no-of-post']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)    
    #pagination Logic
    posts = posts[(page - 1)*int(params['no-of-post']): (page - 1)*int(params['no-of-post']) + int(params['no-of-post'])]
    if (page == 1):
        prev = '#'
        next = "/?page=" + str(page + 1)
    elif (page == last):
        prev = "/?page=" + str(page - 1)
        next = '#'
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    return render_template('index.html', params = params, posts = posts, prev = prev, next = next)


@app.route('/dashboard', methods = ["GET","POST"])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params, posts = posts)
    if request.method == "POST":
        #Redirect to admin
        username = request.form.get('uname')
        userpassword = request.form.get('uPassword')
        if (username == params['admin_user'] and userpassword == params['admin_password']) :
            # set the session variable
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params = params, posts = posts)    
    return render_template('login.html', params = params)



@app.route('/post/<string:post_slug>', methods = ["GET"])
def postFuction(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template('samplePage.html', params = params, post = post)



@app.route('/edit/<string:sno>', methods = ["POST", "GET"])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST' :
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if sno == '0':
                post = Posts(title = box_title,
                    slug = slug,
                    content = content,
                    tagline = tline,
                    img_file = img_file,
                    date = date 
                    )
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/' + sno) 
    post = Posts.query.filter_by(sno = sno).first()
    return render_template('edit.html', params = params, post = post, sno=sno)



@app.route('/about')
def aboutFuction():
    return render_template('about.html', params = params)

    

@app.route('/contact', methods = ["POST", "GET"])
def contactFuction() :
    if request.method == "POST" :
        #add the database
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        #sno,name,email,phone_num,msg,date
        new_msg = Contacts(
            name = name, 
            email = email, 
            phone_num = phone, 
            msg = message
            )   # Create an instance of the Contacts class
        db.session.add(new_msg)    # Adds new Contacts record to database
        db.session.commit()   # Commits all changes
    return render_template('contact.html', params=params)

@app.route('/messages')
def messageFunction() :
    users = Contacts.query.order_by(Contacts.sno)
    contacts = Contacts.query.order_by(Contacts.sno.desc())
    return render_template('messages.html', params = params, contacts = contacts)

@app.route("/msgsent/<string:email>", methods = ['POST', 'GET'])
def msgSendFunction(email):
    if request.method == "POST" :
        #add database
        name = request.form.get('name')
        message = request.form.get('message')
        date = datetime.now()
        new_msg = Messages(
            name = name, 
            message = message,
            date = date
            )   
        db.session.add(new_msg)    
        db.session.commit()  
        msg = Message('Hello ' + name, sender = params['sender_email'], recipients = [email])
        msg.body = message
        mail.send(msg)
        return redirect('/messages') 
    return render_template('messageform.html', params=params, email= email)
  
@app.route('/delete/<string:sno>', methods = ["POST", "GET"])
def deleteFunction(sno):
     if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
     return redirect('/dashboard')


@app.route('/logout')
def logoutFuction():
    session.pop('user')
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run('localhost', 4040, debug=True)
   