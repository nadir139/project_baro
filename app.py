from flask import Flask, render_template,  flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

#create a flask instance
app = Flask(__name__)
app.config['SECRET_KEY'] = "mypassword"

#Create a Form-Class
class NamerForm(FlaskForm):
  name = StringField("what is yout name", validators=[DataRequired()])
  submit = SubmitField("submit")

#Dummy data for job comments (you might want to use a database in a real application)
job_comments = []

@app.route('/')
def index():
    return render_template('index.html', comments=job_comments)

@app.route('/post_comment', methods=['POST'])
def post_comment():
    comment_text = request.form.get('comment')
    job_comments.append(comment_text)
    return redirect(url_for('index'))

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