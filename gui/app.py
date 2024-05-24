import requests
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

# The Username & Password of the currently logged-in User, this is used as a pseudo-cookie, as such this is not session-specific.
username = None
password = None

session_data = dict()


def save_to_session(key, value):
    session_data[key] = value


def load_from_session(key):
    return (
        session_data.pop(key) if key in session_data else None
    )  # Pop to ensure that it is only used once


def successful_request(r: requests.Response) -> bool:
    return r.status_code == 200


@app.route("/")
def home():
    global username

    if username is None:
        return render_template("login.html", username=username, password=password)
    else:
        # ================================
        # FEATURE (list of public events)
        #
        # Retrieve the list of all public events. The webpage expects a list of (title, date, organizer) tuples.
        # Try to keep in mind failure of the underlying microservice
        # =================================

        response = requests.get("http://event-service:5002")

        if successful_request(response):
            public_events = response.json()["events"]
        else:
            public_events = []

        return render_template(
            "home.html", username=username, password=password, events=public_events
        )


@app.route("/event", methods=["POST"])
def create_event():
    title, description, date, publicprivate, invites = (
        request.form["title"],
        request.form["description"],
        request.form["date"],
        request.form["publicprivate"],
        request.form["invites"],
    )
    # ==========================
    # FEATURE (create an event)
    #
    # Given some data, create an event and send out the invites.
    # ==========================
    try:
        requests.post(
            "http://event-service:5002",
            json={
                "title": title,
                "organizer": username,
                "description": description,
                "date": date,
                "publicprivate": publicprivate,
                "invites": invites,
            },
        )
    except requests.exceptions.ConnectionError:
        pass

    return redirect("/")


@app.route("/calendar", methods=["GET", "POST"])
def calendar():
    calendar_user = (
        request.form["calendar_user"] if "calendar_user" in request.form else username
    )

    # ================================
    # FEATURE (calendar based on username)
    #
    # Retrieve the calendar of a certain user. The webpage expects a list of (id, title, date, organizer, status, Public/Private) tuples.
    # Try to keep in mind failure of the underlying microservice
    # =================================

    try:
        response = requests.get(
            f"http://calendar-service:5003/{calendar_user.lower()}",
            params={"user": username.lower()},
        )
        success = successful_request(response)
    except requests.exceptions.ConnectionError:
        success = False

    if success:
        calendar = response.json()["events"]
    else:
        calendar = None

    return render_template(
        "calendar.html",
        username=username,
        password=password,
        calendar_user=calendar_user,
        calendar=calendar,
        success=success,
    )


@app.route("/share", methods=["GET"])
def share_page():
    return render_template(
        "share.html", username=username, password=password, success=None
    )


@app.route("/share", methods=["POST"])
def share():
    share_user = request.form["username"]

    # ========================================
    # FEATURE (share a calendar with a user)
    #
    # Share your calendar with a certain user. Return success = true / false depending on whether the sharing is successful.
    # ========================================

    try:
        response = requests.post(
            "http://calendar-service:5003",
            json={"username": username, "share_with": share_user},
        )
        success = successful_request(response)
    except requests.exceptions.ConnectionError:
        success = False

    return render_template(
        "share.html", username=username, password=password, success=success
    )


@app.route("/event/<eventid>")
def view_event(eventid):
    # ================================
    # FEATURE (event details)
    #
    # Retrieve additional information for a certain event parameterized by an id. The webpage expects a (title, date, organizer, status, (invitee, participating)) tuples.
    # Try to keep in mind failure of the underlying microservice
    # =================================

    try:
        response = requests.get(f"http://event-service:5002/{eventid}")
        success = successful_request(response)
    except requests.exceptions.ConnectionError:
        success = False

    if success:
        event = response.json()
        event = [
            event["event"],
            event["date"],
            event["organizer"],
            event["public"],
            event["invites"],
        ]
    else:
        event = None

    return render_template(
        "event.html", username=username, password=password, event=event, success=success
    )


@app.route("/login", methods=["POST"])
def login():
    req_username, req_password = request.form["username"], request.form["password"]

    # ================================
    # FEATURE (login)
    #
    # send the username and password to the microservice
    # microservice returns True if correct combination, False if otherwise.
    # Also pay attention to the status code returned by the microservice.
    # ================================

    try:
        response = requests.post(
            "http://user-service:5001/login",
            json={"username": req_username, "password": req_password},
        )
        success = successful_request(response)
    except requests.exceptions.ConnectionError:
        success = False

    save_to_session("success", success)
    if success:
        global username, password

        username = req_username
        password = req_password

    return redirect("/")


@app.route("/register", methods=["POST"])
def register():
    req_username, req_password = request.form["username"], request.form["password"]

    # ================================
    # FEATURE (register)
    #
    # send the username and password to the microservice
    # microservice returns True if registration is successful, False if otherwise.
    #
    # Registration is successful if a user with the same username doesn't exist yet.
    # ================================

    try:
        response = requests.post(
            "http://user-service:5001",
            json={"username": req_username, "password": req_password},
        )
        success = successful_request(response)
    except requests.exceptions.ConnectionError:
        success = False

    save_to_session("success", success)
    if success:
        global username, password

        username = req_username
        password = req_password

    return redirect("/")


@app.route("/invites", methods=["GET"])
def invites():
    # ==============================
    # FEATURE (list invites)
    #
    # retrieve a list with all events you are invited to and have not yet responded to
    # ==============================

    try:
        response = requests.get(f"http://event-service:5002/invites/{username}")
        success = successful_request(response)
    except requests.exceptions.ConnectionError:
        success = False

    if success:
        invites = response.json()["invites"]
    else:
        invites = []

    return render_template(
        "invites.html", username=username, password=password, invites=invites
    )


@app.route("/invites", methods=["POST"])
def process_invite():
    eventId, status = request.json["event"], request.json["status"]

    # =======================
    # FEATURE (process invite)
    #
    # process an invite (accept, maybe, don't accept)
    # =======================

    try:
        requests.post(
            f"http://event-service:5002/invites",
            json={"username": username, "status": status, "event_id": int(eventId)},
        )
    except requests.exceptions.ConnectionError:
        pass

    return redirect("/invites")


@app.route("/logout")
def logout():
    global username, password

    username = None
    password = None
    return redirect("/")
