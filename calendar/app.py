import psycopg2
import requests
from flask import Flask, request
from flask_restful import Api, reqparse, Resource
from jsonschema import validate, ValidationError

app = Flask("user-service")
api = Api(app)

conn = psycopg2.connect(
    "dbname=calendar_db user=root password=glowing-banana host=calendar-db"
)
cur = conn.cursor()


class Calendar(Resource):
    def get(self, username):
        try:
            response = requests.get(f"http://user-service:5001/{username}")
        except requests.exceptions.ConnectionError:
            return {"error": "Internal server error"}, 500

        if response.status_code != 200:
            return {"error": "User not found"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("user", required=True, location="args")
        try:
            args = parser.parse_args()
            user = args["user"]
        except Exception:
            return {"error": "Invalid body structure"}, 400

        try:
            cur.execute(
                "SELECT * FROM calendar_shares WHERE owner = %s AND shared_with = %s;",
                (username, user),
            )
            share = cur.fetchone()
        except Exception:
            return {"error": "Internal server error"}, 500

        if share is None:
            return {"error": "User not authorized"}, 403

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
            response = requests.get(f"http://user-service:5001/{username}")
        except requests.exceptions.ConnectionError:
            return {"error": "Internal server error"}, 500

        if response.status_code != 200:
            return {"error": "User not found"}, 404

        try:
            cur.execute(
                "INSERT INTO calendar_shares (owner, shared_with) VALUES (%s, %s);",
                (username, share_with),
            )
        except Exception:
            conn.rollback()
            return {"error": "Internal server error"}, 500

        conn.commit()
        return {"success": True}, 200


api.add_resource(Calendar, "/", "/<string:username>")
