from flask import Flask, render_template, request, redirect, Blueprint
from flask_sqlalchemy import SQLAlchemy
import flask
from random import choice
import flask_login

app = Flask(__name__)
app.secret_key = 'twado'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

routes = Blueprint('routes', __name__, template_folder='templates')
url_for_prefix = ""
url_for = lambda *args, **kwargs: url_for_prefix + flask.url_for(*args, **kwargs)

app.jinja_env.globals['url_for'] = url_for

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    abc = db.Column(db.Text)
    notes = db.Column(db.Text)
    name = db.Column(db.Text)
    category = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

@routes.route('/')
def homepage():
    return render_template("accueil.html")

@routes.route("/deconnection")
def logout():
    if not(hasattr(flask_login.current_user, "username")):
        return redirect(url_for("routes.homepage"))
    flask_login.logout_user()
    return redirect(url_for("routes.homepage"))

@routes.route("/vos_exercices")
def vos_ex():
    if not(hasattr(flask_login.current_user, "username")):
        return redirect(url_for("routes.homepage"))
    exs = Exercise.query.filter_by(user_id=flask_login.current_user.id).all()
    exs = sorted(exs, key=lambda x: x.id)
    cats = {}
    for ex in exs:
        cats.setdefault(ex.category, []).append(ex)
    return render_template("vos_exercices.html", cats=cats)


@routes.route("/editer_exercice")
@routes.route("/editer_exercice/<id>")
def edit_ex(id=None):
    if not(hasattr(flask_login.current_user, "username")):
        return redirect(url_for("routes.homepage"))
    ex = None
    new_ex = id is None
    if id is None:
        ex = Exercise()
    else:
        ex = Exercise.query.filter_by(id=id).first()

    return render_template("editer_exercice.html", exercice=ex, new_ex=new_ex)

@routes.route("/exercice")
@routes.route("/exercice/<id>")
def exercice(id=None):
    if not(hasattr(flask_login.current_user, "username")):
        return redirect(url_for("routes.homepage"))
    ex = Exercise.query.filter_by(id=id).first()
    if not ex or ex.user_id != flask_login.current_user.id:
        return redirect(url_for("routes.tdb"))
    return render_template("exercice.html", exercice=ex)

@routes.route("/rand_exercice")
def rand_ex():
    if not(hasattr(flask_login.current_user, "username")):
        return redirect(url_for("routes.homepage"))
    exs = Exercise.query.filter_by(user_id=flask_login.current_user.id).all()
    if not exs:
        return redirect(url_for("routes.edit_ex"))

    return redirect(url_for("routes.exercice")+"/{}".format(choice(exs).id))

@routes.route("/save_exercice/", methods=["POST"])
@routes.route("/save_exercice/<id>", methods=["POST"])
def save_ex(id=None):
    if not(hasattr(flask_login.current_user, "username")):
        return redirect(url_for("routes.homepage"))
    ex = None
    if id is None:
        ex = Exercise()
    else:
        ex = Exercise.query.filter_by(id=id).first()
    # from IPython import embed; embed()

    content = request.json
    ex.name = content["name"]
    ex.notes = content["notes"]
    ex.abc = content["abc"]
    ex.category = content["category"]
    ex.user_id = flask_login.current_user.id
    db.session.add(ex)
    db.session.commit()
    return str(ex.id)

@routes.route('/tableau_de_bord')
def tdb():
    if not(hasattr(flask_login.current_user, "username")):
        return redirect("/")
    return render_template("tableau_de_bord.html", username=flask_login.current_user.username)

@routes.route('/connection',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("connection.html")

    username = request.form['username']

    if username:
        user = User.query.filter_by(username=username).first()
        if user is None:
            new_user = User(username=username)
            db.session.add(new_user)
            db.session.commit()
            user = new_user
        flask_login.login_user(user, remember=True)

    return redirect(url_for('routes.tdb'))

app.register_blueprint(routes, url_prefix="")
if __name__ == '__main__':
    app.run(debug=True)
