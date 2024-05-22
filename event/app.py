import datetime

import psycopg2
from flask import Flask, request, Response
from flask_restful import Api, Resource
from jsonschema import validate, ValidationError

app = Flask("event-service")
api = Api(app)

conn = psycopg2.connect(
    "dbname=event_db user=root password=glowing-banana host=event-db"
)
cur = conn.cursor()


class Event(Resource):
    def post(self):
        body = request.get_json()
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "organizer": {"type": "string"},
                "description": {"type": "string"},
                "date": {"type": "string"},
                "publicprivate": {"type": "string"},
                "invites": {"type": "string"},
            },
            "required": ["title", "description", "date", "publicprivate", "invites"],
        }
        try:
            validate(body, schema)
        except ValidationError:
            return Response({"error": "Invalid body structure"}, 400)

        title = body["title"]
        organizer = body["organizer"]
        description = body["description"]
        date = body["date"]
        publicprivate = body["publicprivate"]
        invites = body["invites"]

        public = True if publicprivate == "public" else False

        try:
            date = datetime.datetime.fromisoformat(date)
            cur.execute(
                "INSERT INTO Events (title, organizer, date, description, public) VALUES (%s, %s, %s, %s, %s);",
                (title, organizer, date, description, public),
            )
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
            return Response({"error": "Event already exists"}, 409)
        except Exception as e:
            print(e)
            return Response({"error": "Internal server error"}, 500)

        return Response({"success": True}, 200)


api.add_resource(Event, "/event")
