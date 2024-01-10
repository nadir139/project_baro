from flask import Flask, render_template, flash, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from forms import JobForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#password mysql installer : 1234

#create a flask instance
app = Flask(__name__)

#add data base
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/our_users'
#initialize the database
db = SQLAlchemy(app)
#secret key
app.config['SECRET_KEY'] = "mypassword"

#create a model for database
class Users(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(200), nullable=False)
  email = db.Column(db.String(120), nullable=False, unique=True)
  date_added = db.Column(db.DateTime, default=datetime.utcnow)

  #create a string
  def __repr__(self):
    return '<Name %r>' % self.name

#Create a Form-Class
class Userform(FlaskForm):
  name = StringField("Name", validators=[DataRequired()])
  email = StringField("Email", validators=[DataRequired()])
  submit = SubmitField("submit")


#Create a Form-Class
class NamerForm(FlaskForm):
  name = StringField("what is your name", validators=[DataRequired()])
  submit = SubmitField("submit")

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
  name = None
  form = Userform()
  if form.validate_on_submit():
    user = Users.query.filter_by(email=form.email.data).first()
    if user is None:
      user = Users(name=form.name.data, 
      email=form.email.data)
      db.session.add(user)
      db.session.commit()
      name = form.name.data
      form.name.data = ''
      form.email.data = ''
      flash("user added successfully")
  our_users = Users.query.order_by(Users.date_added)
  return (render_template("add_user.html", form=form, name = name, our_users = our_users))

job_comments=[]

@app.route('/')
def index():
    return render_template('index.html', comments=job_comments)

@app.route('/post_comment', methods=['POST'])
def post_comment():
    comment_text = request.form.get('comment')
    timestamp = datetime.now()
    job_comments.append((comment_text, timestamp))
    return redirect(url_for('index'))

# Dummy data for demonstration
jobs = [
    {'title': 'Iluminazione viale Mazzini', 'image_url': 'static\images\illuminazione.jpeg' },
    {'title': 'Canale di scolo Parco Maretta', 'image_url': 'static\images\canale.jpeg'},
    # Add more job data as needed
]

@app.route('/lavori_in_corso', methods=['GET', 'POST'])
def lavori_in_corso():
    form = JobForm()

    if form.validate_on_submit():
        title = form.title.data
        image_url = form.image_url.data
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Add the new job to the jobs list
        jobs.append({'title': title, 'image_url': image_url, 'timestamp': timestamp})

        # Redirect to the same page to prevent form resubmission
        return redirect(url_for('lavori_in_corso'))

    return render_template('lavori_in_corso.html', form=form, jobs=jobs)


@app.route('/user/<name>')
def user(name):
  return render_template("user.html", user_name=name)

#create name page
@app.route('/name', methods=['GET', 'POST'])
def name():
  name = None
  form = NamerForm()
  #validate form
  if form.validate_on_submit():
    name = form.name.data
    form.name.data = ''
    flash("Form submitted Successfully")
  return render_template("name.html", name = name, form = form)

if __name__ == '__main__':
    app.run(debug=True)

@app.errorhandler(404)
def page_not_found(e):
  return render_template("404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
  return render_template("500.html"), 500

