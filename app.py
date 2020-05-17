from flask import Flask, abort, render_template, redirect, url_for, session, request
from flask_dance.contrib.github import make_github_blueprint, github
import functools
import requests
import jq
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv


load_dotenv()

whitelist = [
    "randy3k",
    "randybot"
]

app = Flask(__name__)
# otherwise flask dance thinks it is http
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = os.urandom(20).hex()

if os.environ.get("FLASK_ENV", "development") == "development":
    os.environ['FLASK_ENV'] = "development"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    host = "localhost"
    github_blueprint = make_github_blueprint(
        client_id=os.environ.get("GITHUB_CLIENT_ID_DEVELOP"),
        client_secret=os.environ.get("GITHUB_CLIENT_SECRET_DEVELOP"),
        scope="repo")
else:
    host = "0.0.0.0"
    github_blueprint = make_github_blueprint(
        client_id=os.environ.get("GITHUB_CLIENT_ID"),
        client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
        scope="repo")

app.register_blueprint(github_blueprint, url_prefix='/login')

dir_filter = jq.compile('.[] | select(.type == "dir") | .name')
file_filter = jq.compile('.[] | select(.type == "file") | .name')


def login_required(func):
    @functools.wraps(func)
    def _(*args, **kwargs):
        if not github.authorized:
            session["previous_url"] = request.path
            return(redirect(url_for("github.login")))

        login = session["login"]

        if login not in whitelist:
            abort(403)

        return func(*args, **kwargs)

    return _


def list_directory(owner, repo, subpath):
    token = github.token["access_token"]

    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{subpath}",
        headers={"Authorization": f"token {token}"})
    if r.status_code != 200:
        abort(404)

    d = dict()
    d["owner"] = owner
    d["repo"] = repo
    d["subpath"] = subpath

    j = r.json()
    folders = [d for d in dir_filter.input(j).all() if not d.startswith(".")]
    d["folders"] = folders
    files = [f for f in file_filter.input(j).all() if not f.startswith(".")]
    d["files"] = files
    return render_template("tree.html", **d)


@app.route("/<owner>/<repo>/")
@login_required
def repo_home(owner, repo):
    return list_directory(owner, repo, "")


@app.route("/<owner>/<repo>/<path:subpath>")
@login_required
def view_page(owner, repo, subpath):
    token = github.token["access_token"]

    if subpath.endswith("/"):
        return list_directory(owner, repo, subpath)

    if subpath.endswith(".html"):
        r = requests.get(
            f"https://raw.githubusercontent.com/{owner}/{repo}/master/{subpath}",
            headers={"Authorization": f"token {token}"})
        if r.status_code != 200:
            abort(404)

        return r.text

    return redirect(f"https://github.com/{owner}/{repo}/blob/master/{subpath}")


@app.route("/_go")
@login_required
def go():
    repo = request.args.get("repo", "")
    if repo and repo.startswith("https://github.com/"):
        return redirect(repo[19:])
    return redirect(repo)


@app.route("/_login")
def login():
    return(redirect(url_for("github.login")))


@app.route("/_logout")
def logout():
    if github.authorized:
        session.clear()
    return(redirect(url_for("home")))


@app.route("/")
def home():
    if github.authorized:
        # try three times before we gave up
        for i in range(3):
            resp = github.get("/user")
            if resp.ok:
                break
        if not resp.ok:
            session.clear()
            return redirect(url_for("home"))

        session["login"] = resp.json()["login"]

    if "previous_url" in session:
        previous_url = session["previous_url"]
        session.pop("previous_url", None)
        if github.authorized:
            return(redirect(previous_url))

    login = session["login"] if "login" in session else None
    return render_template(
        "index.html",
        authorized=github.authorized,
        login=login,
        client_id=github_blueprint.client_id)


if __name__ == "__main__":

    app.run(host=host, port=8080)
