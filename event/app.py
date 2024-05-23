import datetime

import psycopg2
import requests
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
        public_private = body["publicprivate"]
        invites = body["invites"]

        public = True if public_private == "public" else False

        try:
            date = datetime.datetime.fromisoformat(date)
            cur.execute(
                "INSERT INTO events (title, organizer, date, description, public) VALUES (%s, %s, %s, %s, %s);",
                (title, organizer, date, description, public),
            )
            cur.execute("SELECT id FROM events ORDER BY id DESC LIMIT 1;")
            event_id = cur.fetchone()[0]
        except psycopg2.IntegrityError:
            conn.rollback()
            return {"error": "Event already exists"}, 409
        except ValueError:
            conn.rollback()
            return {"error": "Invalid date format"}, 400
        except Exception:
            conn.rollback()
            return {"error": "Internal server error"}, 500

        invites = invites.split(";")
        invites = [invite.strip() for invite in invites]
        invites = list(filter(None, invites))
        invalid_user = False
        for invite in invites:
            if invite.lower() == organizer.lower():
                continue

            try:
                response = requests.get(
                    f"http://user-service:5001/user/{invite.lower()}"
                )
            except Exception:
                return {"error": "Internal server error"}, 500

            if response.status_code != 200:
                invalid_user = True
                continue

            try:
                cur.execute(
                    "INSERT INTO invites (event_id, username) VALUES (%s, %s);",
                    (event_id, invite),
                )
            except psycopg2.IntegrityError:
                conn.rollback()
                return {"error": "Invite already exists"}, 409
            except Exception:
                conn.rollback()
                return {"error": "Internal server error"}, 500

        conn.commit()
        if invalid_user:
            return {"error": "Invalid user"}, 400
        else:
            return {"success": True}, 200


api.add_resource(Event, "/event", "/event/<int:event_id>")
