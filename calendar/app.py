import psycopg2
import requests
from flask import Flask, request
from flask_restful import Api, Resource
from jsonschema import validate, ValidationError

app = Flask("user-service")
api = Api(app)

conn = psycopg2.connect("dbname=user_db user=root password=glowing-banana host=user-db")
cur = conn.cursor()


class Calendar(Resource):
    def get(self, username):
        try:
            response = requests.get(f"http://event-service:5002/{username}")
        except requests.exceptions.ConnectionError:
            return {"error": "Internal server error"}, 500

        return response.json(), 200

    def post(self):
        body = request.get_json()
        schema = {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "share_with": {"type": "string"},
            },
            "required": ["username", "share_with"],
        }
        try:
            validate(body, schema)
        except ValidationError:
            return {"error": "Invalid body structure"}, 400

        username = body["username"]
        share_with = body["share_with"]

        try:
            cur.execute(
                "INSERT INTO calendar (username, shared_with) VALUES (%s, %s);",
                (username, share_with),
            )
            conn.commit()
        except Exception:
            return {"error": "Internal server error"}, 500


api.add_resource(Calendar, "/", "/<string:username>")
