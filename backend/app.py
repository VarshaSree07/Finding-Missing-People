                                        
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import googlemaps
import requests
import uuid
import cv2
from facial_recognition import facial_recognition
from video_processor import save_video_file, save_base64_video, iter_video_frames
from face_detector import detect_faces
from tracker import SimpleSORT
from matcher import (
    build_database_embeddings,
    best_match_for_embedding,
    embedding_from_face_rgb,
)
from notification_service import notification_service

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['missing_persons_db']
missing_persons = db['missing_persons']
found_persons = db['found_persons']
matches = db['matches']

# Google Maps API (robust init: ignore missing/invalid keys in dev)
GOOGLE_MAPS_API_KEY = (os.getenv('GOOGLE_MAPS_API_KEY') or '').strip()
gmaps = None
if GOOGLE_MAPS_API_KEY:
    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    except Exception as e:
        print(f"Google Maps client init skipped due to key error: {e}")
        gmaps = None

# Ensure uploads directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to save image and return path
def save_image(image_data, prefix):
    """Save base64 image data to file and return file path"""
    try:
        # Remove data:image/jpeg;base64, prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Generate unique filename
        filename = f"{prefix}_{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Convert to RGB if necessary and save
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(file_path, 'JPEG', quality=85)
        
        return file_path
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

# Helper function to geocode address
def geocode_address(address):
    """Convert address to coordinates using Google Maps API"""
    try:
        if not gmaps:
            return None, None, None
        
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return location['lat'], location['lng'], geocode_result[0]['formatted_address']
        return None, None, None
    except Exception as e:
        print(f"Error geocoding address: {e}")
        return None, None, None

# API Routes

@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API information"""
    return jsonify({
        'message': 'Missing Persons Finder API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/report-missing': 'Report a missing person',
            'POST /api/report-found': 'Report a found person',
            'GET /api/matches': 'Get all matches',
            'GET /api/reports': 'Get all reports',
            'GET /api/missing-persons': 'Get all missing persons',
            'GET /api/found-persons': 'Get all found persons',
            'PUT /api/matches/<match_id>': 'Update match status',
            'POST /api/geocode': 'Geocode an address',
            'POST /api/reverse-geocode': 'Reverse geocode coordinates'
        }
    })

@app.route('/api/report-missing', methods=['POST'])
def report_missing_person():
    """Report a missing person with facial recognition"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'age', 'gender', 'lastSeenLocation', 'image']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Save image
        image_path = save_image(data['image'], 'missing')
        if not image_path:
            return jsonify({'error': 'Failed to save image'}), 500
        
        # Check if face is detected
        if not facial_recognition.detect_face(image_path):
            os.remove(image_path)  # Clean up
            return jsonify({'error': 'No face detected in image'}), 400
        
        # Generate facial embedding
        embedding = facial_recognition.generate_embedding(image_path)
        if embedding is None:
            return jsonify({'error': 'Failed to generate facial embedding'}), 500
        
        # Geocode location
        lat, lng, formatted_address = geocode_address(data['lastSeenLocation'])
        
        # Prepare person data
        person_data = {
            'name': data['name'],
            'age': int(data['age']),
            'gender': data['gender'],
            'lastSeenLocation': data['lastSeenLocation'],
            'latitude': lat,
            'longitude': lng,
            'formatted_address': formatted_address,
            'contactInfo': data.get('contactInfo', ''),  # Add contact info for notifications
            'image_path': image_path,
            'face_embedding': embedding.tolist(),  # Convert numpy array to list for MongoDB
            'created_at': datetime.now(),
            'status': 'missing'
        }
        
        # Store in database
        result = missing_persons.insert_one(person_data)
        person_id = str(result.inserted_id)
        
        return jsonify({
            'id': person_id,
            'message': 'Missing person reported successfully',
            'face_detected': True
        })
        
    except Exception as e:
        print(f"Error in report_missing_person: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/report-found', methods=['POST'])
def report_found_person():
    """Report a found person with facial recognition and matching"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'image' not in data or not data['image']:
            return jsonify({'error': 'Image is required'}), 400
        
        # Save image
        image_path = save_image(data['image'], 'found')
        if not image_path:
            return jsonify({'error': 'Failed to save image'}), 500
        
        # Check if face is detected
        if not facial_recognition.detect_face(image_path):
            os.remove(image_path)  # Clean up
            return jsonify({'error': 'No face detected in image'}), 400
        
        # Generate facial embedding
        embedding = facial_recognition.generate_embedding(image_path)
        if embedding is None:
            return jsonify({'error': 'Failed to generate facial embedding'}), 500
        
        # Get location data (properly convert to float or None)
        def to_float(v):
            try:
                if v is None or v == '' or v == 'null':
                    return None
                return float(v)
            except (TypeError, ValueError):
                return None
        
        raw_lat = data.get('latitude')
        raw_lon = data.get('longitude')
        latitude = to_float(raw_lat)
        longitude = to_float(raw_lon)
        address = data.get('address', '')
        
        # If coordinates provided, reverse geocode to get address
        if latitude is not None and longitude is not None and not address:
            try:
                if gmaps:
                    reverse_result = gmaps.reverse_geocode((latitude, longitude))
                    if reverse_result:
                        address = reverse_result[0]['formatted_address']
            except Exception as e:
                print(f"Reverse geocoding failed: {e}")
        
        # Prepare person data
        person_data = {
            'latitude': latitude,
            'longitude': longitude,
            'address': address,
            'description': data.get('description', ''),
            'image_path': image_path,
            'face_embedding': embedding.tolist(),  # Convert numpy array to list for MongoDB
            'created_at': datetime.now(),
            'status': 'found'
        }
        
        # Store in database
        result = found_persons.insert_one(person_data)
        person_id = str(result.inserted_id)
        
        # Find matches with missing persons (with geolocation filtering)
        missing_persons_list = list(missing_persons.find({'face_embedding': {'$exists': True}}))
        database_embeddings = []
        
        for person in missing_persons_list:
            if person.get('face_embedding'):
                database_embeddings.append({
                    'id': str(person['_id']),
                    'embedding': person['face_embedding'],
                    'lat': person.get('latitude'),
                    'lon': person.get('longitude'),
                    'data': {
                        'name': person.get('name'),
                        'age': person.get('age'),
                        'gender': person.get('gender'),
                        'lastSeenLocation': person.get('lastSeenLocation'),
                        'contactInfo': person.get('contactInfo', ''),
                        'created_at': person.get('created_at')
                    }
                })
        
        # Find top 3 matches with optional geolocation filtering
        # Allow tuning via env var MATCH_THRESHOLD (default 0.6)
        try:
            match_threshold = float(os.getenv('MATCH_THRESHOLD', '0.6'))
        except Exception:
            match_threshold = 0.6

        use_geo_filter = latitude is not None and longitude is not None
        print(f"[match-debug] DB candidates: {len(database_embeddings)} | using_geo: {use_geo_filter} | threshold: {match_threshold}")
        top_matches = facial_recognition.find_top_matches(
            embedding,
            database_embeddings,
            top_k=3,
            threshold=match_threshold,
            query_lat=latitude,
            query_lon=longitude,
            max_distance_km=200 if use_geo_filter else None
        )
        print(f"[match-debug] top_matches found: {len(top_matches)}")

        # Optional fallback: force-create a best-effort match for debugging
        if not top_matches and os.getenv('FORCE_CREATE_MATCH', '').lower() == 'true' and database_embeddings:
            try:
                # Compute cosine similarity to pick best candidate
                def cosine_sim(a, b):
                    a = np.array(a, dtype=float)
                    b = np.array(b, dtype=float)
                    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
                    return float(np.dot(a, b) / denom)

                best = None
                best_score = -1.0
                for cand in database_embeddings:
                    score = cosine_sim(embedding, cand['embedding'])
                    if score > best_score:
                        best_score = score
                        best = cand

                if best is not None:
                    top_matches = [{
                        'id': best['id'],
                        'similarity': best_score,
                        'distance_km': None,
                        'data': best.get('data', {})
                    }]
                    print(f"[match-debug] Fallback created 1 match with similarity {best_score:.3f}")
            except Exception as e:
                print(f"[match-debug] Fallback match failed: {e}")
        
        # Store matches in database and send notifications for high-confidence matches
        created_matches = []
        for match in top_matches:
            match_data = {
                'missing_person_id': match['id'],
                'found_person_id': person_id,
                'similarity_score': match['similarity'],
                'distance_km': match.get('distance_km'),
                'created_at': datetime.now(),
                'status': 'pending'
            }
            
            # Check if match already exists
            existing_match = matches.find_one({
                'missing_person_id': match['id'],
                'found_person_id': person_id
            })
            
            if not existing_match:
                match_result = matches.insert_one(match_data)
                match_id = str(match_result.inserted_id)
                print(f"[match-debug] Inserted match: {match_id} for missing={match['id']} found={person_id} score={match['similarity']}")
                
                created_matches.append({
                    'match_id': match_id,
                    'missing_person_id': match['id'],
                    'similarity': match['similarity'],
                    'distance_km': match.get('distance_km'),
                    'missing_person_data': match['data']
                })
                
                # Send notifications for high-confidence matches (>90%)
                if notification_service.should_send_notification(match['similarity']):
                    _send_high_confidence_notifications(
                        match_id, match['id'], person_id,
                        match['similarity'], match['data']
                    )
        
        return jsonify({
            'id': person_id,
            'message': 'Found person reported successfully',
            'face_detected': True,
            'matches_found': len(created_matches),
            'matches': created_matches
        })
        
    except Exception as e:
        print(f"Error in report_found_person: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/report-found-video', methods=['POST'])
def report_found_video():
    """
    Report a found person (or multiple people) from a video.

    This endpoint:
    - accepts a video file (multipart/form-data) or base64 video in JSON
    - extracts faces from sampled video frames
    - generates embeddings for each detected face
    - matches each face against missing persons
    - stores found_persons + matches in MongoDB
    """
    try:
        # --- 1. Save incoming video (delegated to video_processor) ---
        video_path = None
        data = {}

        # Prefer multipart file upload if present
        if 'video' in request.files:
            video_file = request.files['video']
            if not video_file or video_file.filename == '':
                return jsonify({'error': 'Video file is required'}), 400
            video_path = save_video_file(video_file, prefix='found_video')
        else:
            # Fallback: JSON body with base64 video string
            data = request.get_json() or {}
            video_data = data.get('video')
            if not video_data:
                return jsonify({'error': 'Video is required (file or base64 in JSON)'}), 400
            video_path = save_base64_video(video_data, prefix='found_video')

        if not video_path or not os.path.exists(video_path):
            return jsonify({'error': 'Failed to access saved video'}), 500

        # --- 2. Optional location + metadata (same logic as /api/report-found) ---
        def to_float(v):
            try:
                if v is None or v == '' or v == 'null':
                    return None
                return float(v)
            except (TypeError, ValueError):
                return None

        # For multipart, use request.form; for JSON, we already have data above
        if request.files:
            form = request.form
            raw_lat = form.get('latitude')
            raw_lon = form.get('longitude')
            address = form.get('address', '')
            description = form.get('description', '')
        else:
            raw_lat = data.get('latitude')
            raw_lon = data.get('longitude')
            address = data.get('address', '')
            description = data.get('description', '')

        latitude = to_float(raw_lat)
        longitude = to_float(raw_lon)

        # If coordinates provided but no address, try reverse geocode
        if latitude is not None and longitude is not None and not address:
            try:
                if gmaps:
                    reverse_result = gmaps.reverse_geocode((latitude, longitude))
                    if reverse_result:
                        address = reverse_result[0]['formatted_address']
            except Exception as e:
                print(f"Reverse geocoding failed (video): {e}")

        # --- 3. Scan video frames for faces + track them ---
        max_faces = int(os.getenv('MAX_VIDEO_FACES', '50'))   # safety cap
        target_fps = float(os.getenv('VIDEO_TARGET_FPS', '2.0'))  # frames per second to sample

        tracker = SimpleSORT(
            max_age=int(os.getenv('TRACKER_MAX_AGE', '15')),
            min_hits=int(os.getenv('TRACKER_MIN_HITS', '1')),
            iou_threshold=float(os.getenv('TRACKER_IOU_THRESHOLD', '0.3')),
        )

        # Cache: track_id -> embedding (so we don't recompute per frame)
        embedding_cache = {}

        # For API response
        detected_faces = []  # list of (track_id, embedding, face_image_path, frame_index, match_info)

        # Build DB embeddings once
        database_embeddings = build_database_embeddings(missing_persons)

        try:
            match_threshold = float(os.getenv('VIDEO_MATCH_THRESHOLD', os.getenv('MATCH_THRESHOLD', '0.6')))
        except Exception:
            match_threshold = 0.6

        faces_processed = 0
        all_created_matches = []
        processed_track_ids = set()

        for frame_index, frame_bgr in iter_video_frames(video_path, target_fps=target_fps):
            detections = detect_faces(frame_bgr)
            if not detections:
                continue

            tracks = tracker.update(detections, frame_index)

            for t in tracks:
                if len(detected_faces) >= max_faces:
                    break

                track_id = t.track_id
                # Only process each tracked face once for matching/storage.
                if track_id in processed_track_ids:
                    continue

                # Compute embedding only once per track
                if track_id not in embedding_cache:
                    face_rgb = t.metadata.get('face_rgb')
                    if face_rgb is None:
                        continue
                    emb = embedding_from_face_rgb(face_rgb)
                    if emb is None:
                        continue
                    embedding_cache[track_id] = emb
                else:
                    emb = embedding_cache[track_id]

                # Match against DB
                match = best_match_for_embedding(emb, database_embeddings, threshold=match_threshold)
                if (
                    match is None
                    and os.getenv('FORCE_CREATE_MATCH', '').lower() == 'true'
                    and database_embeddings
                ):
                    # Optional debug fallback: create a best-effort match even below threshold.
                    try:
                        best_cand = None
                        best_score = -1.0
                        for cand in database_embeddings:
                            cand_emb = cand.get('embedding')
                            if cand_emb is None:
                                continue
                            denom = (np.linalg.norm(emb) * np.linalg.norm(cand_emb)) or 1.0
                            score = float(np.dot(emb, cand_emb) / denom)
                            if score > best_score:
                                best_score = score
                                best_cand = cand
                        if best_cand is not None:
                            from matcher import MatchResult
                            match = MatchResult(
                                missing_person_id=best_cand['id'],
                                similarity=best_score,
                                data=best_cand.get('data', {}),
                            )
                    except Exception as e:
                        print(f"[video-match-debug] Fallback match failed: {e}")

                # Save cropped face snapshot
                bbox = t.bbox
                x1, y1, x2, y2 = [int(v) for v in bbox]
                h, w = frame_bgr.shape[:2]
                x1 = max(0, min(x1, w - 1))
                x2 = max(0, min(x2, w))
                y1 = max(0, min(y1, h - 1))
                y2 = max(0, min(y2, h))
                crop = frame_bgr[y1:y2, x1:x2]

                face_filename = f"found_video_{uuid.uuid4().hex}_t{track_id}_f{frame_index}.jpg"
                face_path = os.path.join(UPLOAD_FOLDER, face_filename)
                try:
                    cv2.imwrite(face_path, crop)
                except Exception as e:
                    print(f"Error saving tracked face image from video: {e}")
                    continue

                detected_faces.append((track_id, emb, face_path, frame_index, match))
                processed_track_ids.add(track_id)

            if len(detected_faces) >= max_faces:
                break

        if not detected_faces:
            return jsonify({'error': 'No faces detected in video'}), 400

        # --- 4. Persist found faces + matches to MongoDB ---
        for track_id, embedding, face_path, frame_idx, match in detected_faces:
            faces_processed += 1

            person_data = {
                'latitude': latitude,
                'longitude': longitude,
                'address': address,
                'description': description,
                'image_path': face_path,
                'face_embedding': embedding.tolist(),
                'created_at': datetime.now(),
                'status': 'found',
                'source': 'video',
                'video_path': video_path,
                'frame_index': frame_idx,
                'track_id': track_id,
            }

            result = found_persons.insert_one(person_data)
            person_id = str(result.inserted_id)

            if match is None:
                continue

            match_data = {
                'missing_person_id': match.missing_person_id,
                'found_person_id': person_id,
                'similarity_score': match.similarity,
                'distance_km': None,  # distance optional here; can be added if needed
                'created_at': datetime.now(),
                'status': 'pending',
            }

            existing_match = matches.find_one({
                'missing_person_id': match.missing_person_id,
                'found_person_id': person_id,
            })

            if not existing_match:
                match_result = matches.insert_one(match_data)
                match_id = str(match_result.inserted_id)

                all_created_matches.append({
                    'match_id': match_id,
                    'missing_person_id': match.missing_person_id,
                    'found_person_id': person_id,
                    'similarity': match.similarity,
                    'distance_km': None,
                    'missing_person_data': match.data,
                    'frame_index': frame_idx,
                    'track_id': track_id,
                })

                if notification_service.should_send_notification(match.similarity):
                    _send_high_confidence_notifications(
                        match_id,
                        match.missing_person_id,
                        person_id,
                        match.similarity,
                        match.data,
                    )

        return jsonify({
            'message': 'Video processed successfully',
            'video_path': video_path,
            'faces_detected': len(detected_faces),
            'faces_processed': faces_processed,
            'matches_created': len(all_created_matches),
            'matches': all_created_matches,
        })

    except Exception as e:
        print(f"Error in report_found_video: {e}")
        return jsonify({'error': str(e)}), 500


# ---- Thin wrappers to match requested routes ----

@app.route('/upload-video', methods=['POST'])
def upload_video():
    """
    Upload and process a video for found-person detection.

    This is a thin wrapper around /api/report-found-video so that
    the frontend can call the simpler, non-namespaced route.
    """
    return report_found_video()


@app.route('/process-video', methods=['POST'])
def process_video():
    """
    Alias of /upload-video for compatibility with the requested API.
    """
    return report_found_video()


@app.route('/results', methods=['GET'])
def results():
    """
    Return match results; currently mapped to /api/matches.
    """
    return get_matches()

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """Get all potential matches"""
    try:
        match_list = list(matches.find().sort('created_at', -1))
        for match in match_list:
            match['_id'] = str(match['_id'])
            match['missing_person_id'] = str(match['missing_person_id'])
            match['found_person_id'] = str(match['found_person_id'])
        return jsonify(match_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def get_all_reports():
    """Get all reports (missing + found)"""
    try:
        missing = list(missing_persons.find())
        found = list(found_persons.find())
        
        # Add type field and convert ObjectId to string
        for person in missing:
            person['_id'] = str(person['_id'])
            person['type'] = 'missing'
            
        for person in found:
            person['_id'] = str(person['_id'])
            person['type'] = 'found'
        
        all_reports = missing + found
        # Sort by creation date (newest first)
        all_reports.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify(all_reports)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/missing-persons', methods=['GET'])
def get_missing_persons():
    """Get all missing persons"""
    try:
        people = list(missing_persons.find())
        for person in people:
            person['_id'] = str(person['_id'])
        return jsonify(people)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/found-persons', methods=['GET'])
def get_found_persons():
    """Get all found persons"""
    try:
        people = list(found_persons.find())
        for person in people:
            person['_id'] = str(person['_id'])
        return jsonify(people)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/matches/<match_id>', methods=['PUT'])
def update_match_status(match_id):
    """Update match status (verify/reject)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'verified', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
        
        result = matches.update_one(
            {'_id': ObjectId(match_id)},
            {'$set': {'status': new_status}}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Match not found'}), 404
        
        return jsonify({'message': 'Match status updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/geocode', methods=['POST'])
def geocode_address_endpoint():
    """Convert address to coordinates using Google Maps API"""
    try:
        data = request.get_json()
        address = data.get('address')
        
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        lat, lng, formatted_address = geocode_address(address)
        
        if lat is None or lng is None:
            return jsonify({'error': 'Address not found'}), 404
        
        return jsonify({
            'lat': lat,
            'lng': lng,
            'formatted_address': formatted_address
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reverse-geocode', methods=['POST'])
def reverse_geocode():
    """Convert coordinates to address using Google Maps API"""
    try:
        data = request.get_json()
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not lat or not lng:
            return jsonify({'error': 'Latitude and longitude are required'}), 400
        
        if not gmaps:
            return jsonify({'error': 'Google Maps API not configured'}), 500
        
        reverse_geocode_result = gmaps.reverse_geocode((lat, lng))
        
        if reverse_geocode_result:
            return jsonify({
                'formatted_address': reverse_geocode_result[0]['formatted_address'],
                'address_components': reverse_geocode_result[0]['address_components']
            })
        else:
            return jsonify({'error': 'Location not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _send_high_confidence_notifications(match_id, missing_person_id, found_person_id, 
                                       similarity_score, missing_person_data):
    """
    Send notifications for high-confidence matches
    
    Args:
        match_id (str): Match ID
        missing_person_id (str): Missing person ID
        found_person_id (str): Found person ID
        similarity_score (float): Match confidence score
        missing_person_data (dict): Missing person data including contact info
    """
    try:
        # Get missing person details from database
        missing_person = missing_persons.find_one({'_id': ObjectId(missing_person_id)})
        if not missing_person:
            return
        
        # Get found person details from database
        found_person = found_persons.find_one({'_id': ObjectId(found_person_id)})
        if not found_person:
            return
        
        contact_info = missing_person.get('contactInfo', '')
        missing_person_name = missing_person.get('name', 'Unknown')
        
        # Prepare found person data for notification
        found_person_data = {
            'address': found_person.get('address', 'Location not specified'),
            'created_at': found_person.get('created_at', 'Unknown')
        }
        
        # Send email notification if contact info contains email
        if '@' in contact_info:
            email_success = notification_service.send_email_notification(
                to_email=contact_info,
                to_name=missing_person_name,
                missing_person_name=missing_person_name,
                found_person_data=found_person_data,
                similarity_score=similarity_score,
                match_id=match_id
            )
            notification_service.log_notification(
                match_id, 'email', contact_info, email_success
            )
        
        # Send SMS notification if contact info looks like a phone number
        elif contact_info.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            sms_success = notification_service.send_sms_notification(
                to_phone=contact_info,
                missing_person_name=missing_person_name,
                similarity_score=similarity_score,
                match_id=match_id
            )
            notification_service.log_notification(
                match_id, 'sms', contact_info, sms_success
            )
        
        # Log the high-confidence match
        print(f"High-confidence match found: {missing_person_name} - {similarity_score:.1%} confidence")
        
    except Exception as e:
        print(f"Error sending high-confidence notifications: {e}")
        notification_service.log_notification(
            match_id, 'error', 'system', False, str(e)
        )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)