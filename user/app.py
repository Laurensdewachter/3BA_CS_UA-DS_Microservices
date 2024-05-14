import psycopg2
from flask import Flask, request, Response
from flask_restful import Api, Resource
from jsonschema import validate, ValidationError

app = Flask("User")
api = Api(app)

conn = psycopg2.connect("dbname=user_db user=root password=glowing-banana host=user-db")
cur = conn.cursor()


class User(Resource):
    def post(self) -> Response:
        schema = {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["username", "password"],
        }
        try:
            body = request.get_json()
            validate(body, schema)
        except ValidationError as e:
            return Response({"error": "Invalid body structure"}, status=400)

        username = body["username"]
        password = body["password"]

        try:
            cur.execute(
                "INSERT INTO Users (username, password) VALUES (%s, %s);",
                (username, password),
            )
            conn.commit()
        except psycopg2.IntegrityError as e:
            conn.rollback()
            print(e)
            return Response({"error": "User already exists"}, status=409)
        except Exception as e:
            print(e)
            return Response({"error": "Internal server error"}, status=500)

        return Response({"success": True}, status=200)


api.add_resource(User, "/user")

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5001)
