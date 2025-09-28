#!/usr/bin/env python3

from flask import Flask, jsonify, session, make_response, request
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)

# CLEAR SESSION
class ClearSession(Resource):
    def delete(self):
        session['page_views'] = 0
        session.pop('user_id', None)
        return {}, 204


# INDEX ARTICLES
class IndexArticle(Resource):
    def get(self):
        articles = Article.query.all()
        result = [ {"id": a.id, "title": a.title, "content": a.content} for a in articles ]
        return result, 200


# SHOW ARTICLE WITH PAYWALL
class ShowArticle(Resource):
    def get(self, id):
        # Initialize page_views
        session['page_views'] = session.get('page_views', 0)
        session['page_views'] += 1

        # Check paywall
        if session['page_views'] > 3:
            return {'message': 'Maximum pageview limit reached'}, 401

        # Fetch article safely
        article = Article.query.get_or_404(id)
        article_data = {"id": article.id, "title": article.title, "content": article.content}

        return make_response(jsonify(article_data), 200)


# LOGIN
class Login(Resource):
    def post(self):
        data = request.get_json()
        if not data or 'username' not in data:
            return {"message": "Username required"}, 400

        user = User.query.filter_by(username=data['username']).first()
        if not user:
            return {"message": "User not found"}, 404

        session['user_id'] = user.id
        return {"id": user.id, "username": user.username}, 200


# LOGOUT
class Logout(Resource):
    def delete(self):
        session.pop('user_id', None)
        return {}, 204


# CHECK SESSION
class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {}, 401

        user = User.query.get(user_id)
        if not user:
            return {}, 401

        return {"id": user.id, "username": user.username}, 200


# ROUTES
api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
