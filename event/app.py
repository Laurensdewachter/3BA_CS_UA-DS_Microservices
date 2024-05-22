import datetime

import psycopg2
from flask import Flask, request
from flask_restful import Api, Resource
from jsonschema import validate, ValidationError

app = Flask("event-service")
api = Api(app)

conn = psycopg2.connect(
    "dbname=event_db user=root password=glowing-banana host=event-db"
)
cur = conn.cursor()


class Event(Resource):
    def get(self, event_id):
        try:
            cur.execute(
                "SELECT (title, date, organizer, public) FROM events WHERE id = %s;",
                (event_id,),
            )
            event = cur.fetchone()
        except Exception:
            return {"error": "Internal server error"}, 500

        if event is None:
            return {"error": "Event not found"}, 404

        return {"event": event}, 200

    def get(self):
        try:
            cur.execute(
                "SELECT title, date, organizer FROM events WHERE public = TRUE;"
            )
            event_entries = cur.fetchall()
        except Exception:
            return {"error": "Internal server error"}, 500

        if event_entries is None:
            events = []
        else:
            events = []
            for entry in event_entries:
                events.append(
                    (
                        entry[0],
                        entry[1].strftime("%d-%m-%Y"),
                        entry[2],
                    )
                )

        return {"events": events}, 200

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
            return {"error": "Invalid body structure"}, 400

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
                "INSERT INTO events (title, organizer, date, description, public) VALUES (%s, %s, %s, %s, %s);",
                (title, organizer, date, description, public),
            )
            conn.commit()
        except psycopg2.IntegrityError:
            conn.rollback()
            return {"error": "Event already exists"}, 409
        except Exception as e:
            print(e)
            return {"error": "Internal server error"}, 500

        return {"success": True}, 200


api.add_resource(Event, "/event", "/event/<int:event_id>")
