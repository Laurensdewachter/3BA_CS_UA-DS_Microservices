import psycopg2
import requests
from flask import Flask, request
from flask_restful import Api, Resource
from jsonschema import validate, ValidationError

app = Flask("user-service")
api = Api(app)


class Calendar(Resource):
    def get(self, username):
        try:
            response = requests.get(f"http://event-service:5002/{username}")
        except requests.exceptions.ConnectionError:
            return {"error": "Internal server error"}, 500

        return response.json(), 200


api.add_resource(Calendar, "/<string:username>")
