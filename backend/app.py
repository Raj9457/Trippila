from flask import Flask, jsonify, request
from bson.objectid import ObjectId
from bson import ObjectId, json_util

from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB
mongo_url = os.environ.get("mongoUrl")
client = MongoClient(mongo_url)
db = client["Trippila"]  

# User Endpoints
# Get all users
@app.route('/users', methods=['GET'])
def get_users():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    users = list(db.users.find().skip((page - 1) * per_page).limit(per_page))
    total_users = db.users.count_documents({})

    for user in users:
        user['_id'] = str(user['_id'])

    return jsonify(users=users, total_users=total_users)


# Get a user by ID
@app.route('/users/<string:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        user['_id'] = str(user['_id'])
        return jsonify(user)
    else:
        return jsonify({"message": "User not found"}), 404

# Create a new user
@app.route('/users', methods=['POST'])
def create_user():
    user_data = request.get_json()
    email = user_data.get('email')

    # Check if email already exists
    existing_user = db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"message": "User already exists with this email"}), 400

    result = db.users.insert_one(user_data)
    return jsonify({"message": "User created successfully", "user_id": str(result.inserted_id)}), 201

@app.route('/login_user', methods=['POST'])
def login():
    user_data = request.get_json()
    email = user_data.get('email')
    password = user_data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required!'})

    user = db.users.find_one({'email': email, 'password': password})
    if not user:
        return jsonify({'message': 'Invalid credentials!'})

    return jsonify({'message': 'Login successful!', "user_id": str(user['_id'])})

# Update a user by ID
@app.route('/users/<string:user_id>', methods=['PUT'])
def update_user(user_id):
    updated_data = request.get_json()
    result = db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updated_data})
    if result.matched_count > 0:
        return jsonify({"message": "User updated successfully"})
    else:
        return jsonify({"message": "User not found"}), 404

# Delete a user by ID
@app.route('/users/<string:user_id>', methods=['DELETE'])
def delete_user(user_id):
    result = db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count > 0:
        return jsonify({"message": "User deleted successfully"})
    else:
        return jsonify({"message": "User not found"}), 404
        

# Route for filtering users based on criteria
@app.route('/users/filter', methods=['GET'])
def filter_users():
    try:
        # Get query parameters from the request
        username = request.args.get('username')
        email = request.args.get('email')
        date_of_birth = request.args.get('date_of_birth')
        gender = request.args.get('gender')
        membership = request.args.get('membership')
        user_status = request.args.get('user_status')

        # Create a filter dictionary based on the provided query parameters
        filter = {}
        if username:
            filter['username'] = username
        if email:
            filter['email'] = email
        if date_of_birth:
            filter['date_of_birth'] = date_of_birth
        if gender:
            filter['gender'] = gender
        if membership:
            filter['membership'] = membership
        if user_status:
            filter['user_status'] = user_status

        # Use the filter dictionary to query the database for filtered users
        filtered_users = list(db.users.find(filter))
        for user in filtered_users:
            user['_id'] = str(user['_id'])

        # Convert the list of users to a JSON response
        return jsonify(users=filtered_users)

    except Exception as e:
        print(e)
        return jsonify(error='Internal server error'), 500

# //********************Movies and show management****************//

@app.route('/movies', methods=['GET'])
def get_all_movies():
    movies = list(db["movies"].find())
    # Convert ObjectId to a serializable format
    for movie in movies:
        movie['_id'] = str(movie['_id'])
    return json_util.dumps(movies), 200

@app.route('/movies/<string:movie_id>', methods=['GET'])
def get_movie(movie_id):
    movie = db["movies"].find_one({"_id": ObjectId(movie_id)})
    if movie:
        movie['_id'] = str(movie['_id'])
        return jsonify(movie), 200
    else:
        return jsonify({"message": "Movie not found"}), 404

@app.route('/movies', methods=['POST'])
def add_movie():
    data = request.json
    title = data.get('title')
    imageurl = data.get('imageurl')
    city = data.get('city')
    language = data.get('language')

    # Insert the new movie into the 'movies' collection
    movie_data = {
        "title": title,
        "imageurl": imageurl,
        "city": city,
        "language": language
    }
    movie_id = db["movies"].insert_one(movie_data).inserted_id

    return jsonify({"message": "Movie added successfully", "movie_id": str(movie_id)}), 201

@app.route('/movies/<string:movie_id>', methods=['PUT'])
def update_movie(movie_id):
    data = request.json
    title = data.get('title')
    imageurl = data.get('imageurl')
    city = data.get('city')
    language = data.get('language')

    # Update the movie in the 'movies' collection
    result = db["movies"].update_one({"_id": movie_id}, {"$set": {
        "title": title,
        "imageurl": imageurl,
        "city": city,
        "language": language
    }})

    if result.modified_count == 1:
        return jsonify({"message": "Movie updated successfully"}), 200
    else:
        return jsonify({"message": "Movie not found"}), 404

@app.route('/movies/<string:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    # Delete the movie from the 'movies' collection
    result = db["movies"].delete_one({"_id": ObjectId(movie_id)})

    if result.deleted_count == 1:
        return jsonify({"message": "Movie deleted successfully"}), 200
    else:
        return jsonify({"message": "Movie not found"}), 404

@app.route('/shows', methods=['POST'])
def add_show():
    data = request.json
    movie_id = data.get('movie_id')
    timings = data.get('timings')
    category = data.get('category')

    # Assuming you have a 'shows' collection in your MongoDB database
    shows_collection = db["shows"]

    movie_id_obj = ObjectId(movie_id)
    # Check if the movie_id exists in the 'movies' collection
    movie = db["movies"].find_one({"_id": movie_id_obj})
    print("movie",movie)
    if not movie:
        return jsonify({"message": "Movie not found"}), 404

    # Insert the new show into the 'shows' collection
    show_data = {
        "movie_id": movie_id,
        "timings": timings,
        "category": category
    }
    show_id = shows_collection.insert_one(show_data).inserted_id

    return jsonify({"message": "Show added successfully", "show_id": str(show_id)}), 201

@app.route('/shows', methods=['GET'])
def get_all_shows():
    shows = list(db["shows"].find())
    # Convert ObjectId to a serializable format
    for show in shows:
        show['_id'] = str(show['_id'])
        show['movie_id'] = str(show['movie_id'])
    return json_util.dumps(shows), 200

@app.route('/shows/<string:show_id>', methods=['GET'])
def get_show(show_id):
    show = db["shows"].find_one({"_id": ObjectId(show_id)})
    if show:
        show['_id'] = str(show['_id'])
        show['movie_id'] = str(show['movie_id'])
        return jsonify(show), 200
    else:
        return jsonify({"message": "Show not found"}), 404


# //*******************************Events******************************//       


@app.route('/events', methods=['POST'])
def create_event():
    data = request.json
    title = data.get('title')
    image = data.get('image')
    city = data.get('city')
    price = data.get('price')
    date = data.get('date')

    event_data = {
        "title": title,
        "image": image,
        "city": city,
        "price": price,
        "date": date
    }
    event_id = db.events.insert_one(event_data).inserted_id

    return jsonify({"message": "Event created successfully", "event_id": str(event_id)}), 201

@app.route('/events', methods=['GET'])
def get_all_events():
    events = list(db.events.find())
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify(events), 200

@app.route('/events/<string:event_id>', methods=['GET'])
def get_event(event_id):
    event = db.events.find_one({"_id": ObjectId(event_id)})
    if event:
        event['_id'] = str(event['_id'])
        return jsonify(event), 200
    else:
        return jsonify({"message": "Event not found"}), 404

@app.route('/events/<string:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.json
    updated_fields = {}

    title = data.get('title')
    if title:
        updated_fields['title'] = title

    image = data.get('image')
    if image:
        updated_fields['image'] = image

    city = data.get('city')
    if city:
        updated_fields['city'] = city

    price = data.get('price')
    if price:
        updated_fields['price'] = price

    date = data.get('date')
    if date:
        updated_fields['date'] = date

    if not updated_fields:
        return jsonify({"message": "No update data provided"}), 400

    result = db.events.update_one({"_id": ObjectId(event_id)}, {"$set": updated_fields})

    if result.modified_count == 1:
        return jsonify({"message": "Event updated successfully"}), 200
    else:
        return jsonify({"message": "Event not found"}), 404


@app.route('/events/<string:event_id>', methods=['DELETE'])
def delete_event(event_id):
    result = db.events.delete_one({"_id": ObjectId(event_id)})

    if result.deleted_count == 1:
        return jsonify({"message": "Event deleted successfully"}), 200
    else:
        return jsonify({"message": "Event not found"}), 404


# //**********************Participants******************//        

@app.route('/participants', methods=['POST'])
def add_participant():
    data = request.json
    event_id = data.get('event_id')
    user_id = data.get('user_id')

    # Check if the event_id exists in the 'events' collection
    event = db.events.find_one({"_id": ObjectId(event_id)})
    if not event:
        return jsonify({"message": "Event not found"}), 404

    # Check if the event_id is already present in the 'participants' collection
    participant = db.participants.find_one({"event_id": event_id})
    if participant:
        # If the user_id is not already in the user_ids array, add it
        if user_id not in participant['user_ids']:
            result = db.participants.update_one({"event_id": event_id}, {"$addToSet": {"user_ids": user_id}})
        else:
            return jsonify({"message": "User is already a participant in the event"}), 200
    else:
        # If the event_id is not present in the 'participants' collection, create a new entry
        participant_data = {
            "event_id": event_id,
            "user_ids": [user_id]
        }
        result = db.participants.insert_one(participant_data)

    if result.acknowledged:
        return jsonify({"message": "Participant added successfully"}), 201
    else:
        return jsonify({"message": "Failed to add participant"}), 500


@app.route('/participants', methods=['GET'])
def get_all_participants():
    participants = list(db.participants.find())
    for participant in participants:
        participant['_id'] = str(participant['_id'])
    return jsonify(participants), 200


if __name__ == '__main__':
    app.run(debug=True)