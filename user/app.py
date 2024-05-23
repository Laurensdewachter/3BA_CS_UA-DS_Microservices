import psycopg2
from flask import Flask, request
from flask_restful import Api, Resource
from jsonschema import validate, ValidationError

app = Flask("user-service")
api = Api(app)

conn = psycopg2.connect("dbname=user_db user=root password=glowing-banana host=user-db")
cur = conn.cursor()


def check_schema(body):
    schema = {
        "type": "object",
        "properties": {
            "username": {"type": "string"},
            "password": {"type": "string"},
        },
        "required": ["username", "password"],
    }
    try:
        validate(body, schema)
    except ValidationError as e:
        raise e


class User(Resource):
    def get(self, username):
        try:
            cur.execute("SELECT * FROM users WHERE username = %s;", (username.lower(),))
            user = cur.fetchone()
        except Exception:
            return {"error": "Internal server error"}, 500

        if user is None:
            return {"error": "User not found"}, 404

        return {"user": user}, 200

    def post(self):
        body = request.get_json()
        try:
            check_schema(body)
        except ValidationError:
            return {"error": "Invalid body structure"}, 400

        username = body["username"].lower()
        password = body["password"]

        try:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s);",
                (username, password),
            )
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
            return {"error": "User already exists"}, 409
        except Exception:
            return {"error": "Internal server error"}, 500

        return {"success": True}, 200


class Login(Resource):
    def post(self):
        body = request.get_json()
        try:
            check_schema(body)
        except ValidationError:
            return {"error": "Invalid body structure"}, 400

        username = body["username"].lower()
        password = body["password"]

        try:
            cur.execute("SELECT password FROM users WHERE username = %s;", (username,))
            user = cur.fetchone()
        except Exception:
            return {"error": "Internal server error"}, 500

        if user is None:
            return {"error": "User does not exist"}, 404

        if user[0] != password:
            return {"error": "Incorrect password"}, 401
        return {"success": True}, 200


api.add_resource(User, "/", "/<string:username>")
api.add_resource(Login, "/login")
