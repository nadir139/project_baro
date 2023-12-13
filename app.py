from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dummy data for job comments (you might want to use a database in a real application)
job_comments = []

@app.route('/')
def index():
    return render_template('index.html', comments=job_comments)

@app.route('/post_comment', methods=['POST'])
def post_comment():
    comment_text = request.form.get('comment')
    job_comments.append(comment_text)
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
  return render_template("404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
  return render_template("500.html"), 500


if __name__ == '__main__':
    app.run(debug=True)
