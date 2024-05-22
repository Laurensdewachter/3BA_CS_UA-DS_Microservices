import psycopg2
from flask import Flask, request, Response
from flask_restful import Api, Resource
from jsonschema import validate, ValidationError

app = Flask("User")
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
    def get(self) -> Response:
        body = request.get_json()
        try:
            check_schema(body)
        except ValidationError:
            return Response({"error": "Invalid body structure"}, status=400)

        username = body["username"]
        password = body["password"]

        try:
            cur.execute("SELECT password FROM users where username = %s;", (username,))
            user = cur.fetchone()
        except Exception as e:
            return Response({"error": "Internal server error"}, status=500)

        if user is None:
            return Response({"error": "User does not exist"}, status=404)

        if user[0] != password:
            return Response({"error": "Incorrect password"}, status=401)
        return Response({"success": True}, status=200)

    def post(self) -> Response:
        body = request.get_json()
        try:
            check_schema(body)
        except ValidationError:
            return Response({"error": "Invalid body structure"}, status=400)

        username = body["username"]
        password = body["password"]

        try:
            cur.execute(
                "INSERT INTO Users (username, password) VALUES (%s, %s);",
                (username, password),
            )
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
            return Response({"error": "User already exists"}, status=409)
        except Exception:
            return Response({"error": "Internal server error"}, status=500)

        return Response({"success": True}, status=200)


api.add_resource(User, "/user")
