# API Endpoints
## User service
### POST /
Creates a new user.
#### Request body:
| Key      | Field                         |
|----------|-------------------------------|
| username | The username for the new user |
| password | The password for the new user |

#### Response
Returns `success: True` if successful
#### Return codes
- 200: User created
- 400: Invalid body
- 409: User already exists

### GET /{username}
Check if a user exists.
#### Response
Returns `success: True` if the user exists
#### Return codes
- 200: User exists
- 404: User does not exist

### POST /login
Logs in a user.
#### Request body:
| Key      | Field                         |
|----------|-------------------------------|
| username | The username for the new user |
| password | The password for the new user |

#### Response
Returns `success: True` if successful
#### Return codes
- 200: Login successful
- 400: Invalid body
- 401: Wrong password
- 404: User does not exist

## Event service
### GET /
Get all public events.
#### Response
Returns a list of all public events
#### Return codes
- 200: Events returned

### POST /
Create a new event.
#### Request body:
| Key           | Field                                  |
|---------------|----------------------------------------|
| title         | The name of the event                  |
| date          | The date of the event                  |
| description   | A description of the event             |
| publicprivate | Whether the event is public or private |
| organizer     | The organizer of the event             |
| invites       | A list of users to invite to the event |

#### Response
Returns `success: True` if successful
#### Return codes
- 200: Event created
- 400: Invalid body or invited user does not exist

### GET /{event_id}
Get details of an event by its ID.
#### Response
Returns the details of the event
#### Return codes
- 200: Event details returned
- 404: Event does not exist

### GET /{username}
Get all events of a user.
#### Response
Returns a list of all events the user is invited to
#### Return codes
- 200: Events returned

### GET /invites/{username}
Get all events a user is invited to.
#### Response
Returns a list of all events the user is invited to
#### Return codes
- 200: Events returned

### POST /invite
Change response status for an invitation.
#### Request body:
| Key      | Field                              |
|----------|------------------------------------|
| event_id | The ID of the event                |
| username | The username of the user to invite |
| status   | The response status                |

#### Response
Returns `success: True` if successful
#### Return codes
- 200: Response status changed
- 400: Invalid body

## Calendar service
### GET /{username}
Get the calendar of a user.
#### Response
Returns a list of all events the user is invited to
#### Return codes
- 200: Calendar returned
- 403: Not authorized
- 404: User does not exist

### POST /
Share a calendar.
#### Request body:
| Key        | Field                                   |
|------------|-----------------------------------------|
| username   | The username of the user                |
| share_with | The username to share the calendar with |

#### Response
Returns `success: True` if successful
#### Return codes
- 200: Calendar shared
- 400: Invalid body
- 404: User does not exist
