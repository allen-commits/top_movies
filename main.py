from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os

db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SQL_KEY']
Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies_database.db"
db.init_app(app)

TMDB_API_KEY = os.environ['TMDB_API_KEY']


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer)
    description = db.Column(db.String)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String)
    img_url = db.Column(db.String)


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )

with app.app_context():
    db.create_all()


class editForm(FlaskForm):
    rating = FloatField('Your Rating Out of 10. Ex: 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit_edit = SubmitField(label="Done")


class addForm(FlaskForm):
    movie_title = StringField('Title', validators=[DataRequired()])
    submit_add = SubmitField(label="Add Movie")


@app.route("/")
def home():
    """This queries the database, takes the results and orders them according to rating."""
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", all_movies=all_movies)


@app.route('/edit/<num>', methods=('GET', 'POST'))
def edit(num):
    """This allows the user to edit the rating and review."""
    movie = db.get_or_404(Movie, num)
    form = editForm()
    if request.method == 'POST':
        # gets the rating from the form
        movie_rating = form.rating.data
        movie_review = form.review.data
        # gets the movie from the database
        movie = db.get_or_404(Movie, num)
        # updates the movies objects rating and review values with values from forms
        movie.rating = movie_rating
        movie.review = movie_review
        # commit changes
        db.session.commit()
        return redirect((url_for("home")))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete():
    """This method is used to delete the movie from the database."""
    movie_id = request.args.get("movie_id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect((url_for("home")))


@app.route("/add", methods=["GET", "POST"])
def add():
    """This method is used to add movies to the database"""
    form_add = addForm()
    if request.method == 'POST':
        movie_title = form_add.movie_title.data
        return redirect((url_for("select", movie_title=movie_title)))
    return render_template("add.html", form=form_add)


@app.route("/select")
def select():
    """This searches The Movie Data Base via API and returns the results in a list."""
    movie_title = request.args.get("movie_title")
    parameters = {
        "query": movie_title,
        "page": 1,
        "language": "en",
    }
    url = "https://api.themoviedb.org/3/search/movie"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }

    response = requests.get(url, params=parameters, headers=headers)
    response.raise_for_status()
    movie_dict = response.json()
    list_of_movies = []
    poster_path_url = "https://image.tmdb.org/t/p/w185/"
    for i in movie_dict["results"]:
        new_movie_object = Movie(title=i["original_title"],
                                 year=i["release_date"],
                                 id=i["id"])
        list_of_movies.append(new_movie_object)

    return render_template("select.html", list_of_movies=list_of_movies)


@app.route("/find")
def find():
    """This takes the movie the user selects and gets additional information about it via API.
    It then adds the movie into the database, and redirects the user to the edit page.
    The redirection is necessary because database lacks a review and rating."""
    movie_id = request.args.get("movie_id")
    print(movie_id)
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }

    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)

    poster_path = data['poster_path']
    poster_path_complete = f"https://image.tmdb.org/t/p/w500/{poster_path}"
    original_title = data['original_title']
    description = data['overview']
    release_date = data["release_date"]

    selected_movie = Movie(id=movie_id,
                           title=original_title,
                           year=release_date,
                           description=description,
                           img_url=poster_path_complete)

    db.session.add(selected_movie)
    db.session.commit()

    return redirect(url_for("edit", num=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
