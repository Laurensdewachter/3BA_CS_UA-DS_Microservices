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
    def get(self):
        try:
            cur.execute(
                "SELECT title, date, organizer FROM events WHERE public = TRUE;"
            )
            event_entries = cur.fetchall()
        except Exception:
            return {"error": "Internal server error"}, 500

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
                response = requests.get(f"http://user-service:5001/{invite.lower()}")
            except requests.exceptions.ConnectionError:
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


class EventDetails(Resource):
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

        return {"event": event[0]}, 200


class UserEvents(Resource):
    def get(self, username):
        try:
            cur.execute(
                "SELECT (event_id, response) FROM invites WHERE username = %s AND response = %s OR response = %s;",
                (
                    username,
                    "ACCEPTED",
                    "MAYBE",
                ),
            )
            event_ids = cur.fetchall()
        except Exception:
            return {"error": "Internal server error"}, 500

        events = []
        for event_entries in event_ids:
            try:
                event_id = int(event_entries[0][1:-1].split(",")[0])
                status = event_entries[0][1:-1].split(",")[1]
                cur.execute(
                    "SELECT (id, title, date, organizer, public) FROM events WHERE id = %s;",
                    (event_id,),
                )
                entry = cur.fetchone()

                entry_str = entry[0][1:-1]
                events.append(
                    (
                        entry_str.split(",")[0],
                        entry_str.split(",")[1],
                        datetime.datetime.fromisoformat(
                            entry_str.split(",")[2][1:-1]
                        ).strftime("%d-%m-%Y"),
                        entry_str.split(",")[3],
                        "Going" if status == "ACCEPTED" else "Maybe",
                        "Public" if entry_str.split(",")[4] == "f" else "Private",
                    )
                )
            except Exception:
                return {"error": "Internal server error"}, 500

        return {"events": events}, 200


class Invite(Resource):
    def get(self, username):
        try:
            cur.execute(
                "SELECT event_id FROM invites WHERE username = %s AND response = %s;",
                (
                    username,
                    "NO_RESPONSE",
                ),
            )
            invites_entries = cur.fetchall()
        except Exception:
            return {"error": "Internal server error"}, 500

        invites = []
        for entry in invites_entries:
            try:
                response = requests.get(f"http://event-service:5002/{entry[0]}").json()[
                    "event"
                ]
            except requests.exceptions.ConnectionError:
                return {"error": "Internal server error"}, 500
            response = response[1:-1]
            title = response.split(",")[0]
            date = response.split(",")[1][1:-1].split(" ")[0]
            organizer = response.split(",")[2]
            public = response.split(",")[3]

            public = "public" if public == "t" else "private"
            date = datetime.datetime.fromisoformat(date).strftime("%d-%m-%Y")

            invites.append((entry[0], title, date, organizer, public))

        return {"invites": invites}, 200

    def post(self):
        body = request.get_json()
        schema = {
            "type": "object",
            "properties": {
                "event_id": {"type": "integer"},
                "status": {"type": "string"},
                "username": {"type": "string"},
            },
            "required": ["event_id", "status", "username"],
        }
        try:
            validate(body, schema)
        except ValidationError:
            return {"error": "Invalid body structure"}, 400

        event_id = body["event_id"]
        status = body["status"]
        username = body["username"]

        match status:
            case "Participate":
                status = "ACCEPTED"
            case "Don't Participate":
                status = "DECLINED"
            case "Maybe Participate":
                status = "MAYBE"
            case _:
                return {"error": "Invalid status"}, 400

        try:
            cur.execute(
                "UPDATE invites SET response = %s WHERE event_id = %s AND username = %s;",
                (status, event_id, username),
            )
        except Exception:
            conn.rollback()
            return {"error": "Internal server error"}, 500

        conn.commit()
        return {"success": True}, 200


api.add_resource(Event, "/")
api.add_resource(EventDetails, "/<int:event_id>")
api.add_resource(UserEvents, "/<string:username>")
api.add_resource(Invite, "/invites", "/invites/<string:username>")
