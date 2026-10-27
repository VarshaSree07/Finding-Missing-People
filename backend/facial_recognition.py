import numpy as np
import cv2
from PIL import Image
import os
import math

# Try to import DeepFace, but fail gracefully so the backend can still start
try:
    from deepface import DeepFace  # type: ignore
except Exception as e:
    DeepFace = None  # type: ignore
    print(f"[facial_recognition] Warning: DeepFace could not be imported: {e}")


class FacialRecognition:
    def __init__(self, model_name='Facenet'):
        """
        Initialize facial recognition with specified model
        Available models: VGG-Face, Facenet, OpenFace, DeepFace, DeepID, ArcFace
        """
        self.model_name = model_name

    def generate_embedding(self, image_path):
        """
        Generate facial embedding from image path

        Args:
            image_path (str): Path to the image file

        Returns:
            numpy.ndarray: Face embedding vector or None if no face detected
        """
        try:
            if DeepFace is None:
                print("[facial_recognition] DeepFace unavailable, cannot generate embedding.")
                return None
            # Verify image exists
            if not os.path.exists(image_path):
                print(f"Image file not found: {image_path}")
                return None

            # Generate embedding using DeepFace
            embedding = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                enforce_detection=True,
                detector_backend='opencv'
            )[0]['embedding']

            return np.array(embedding)

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def generate_embedding_from_array(self, image_array):
        """
        Generate facial embedding directly from a numpy image array.

        This is useful for video frames or already-cropped face images.
        """
        try:
            if DeepFace is None:
                print("[facial_recognition] DeepFace unavailable, cannot generate embedding from array.")
                return None
            if image_array is None:
                return None

            embedding = DeepFace.represent(
                img_path=image_array,
                model_name=self.model_name,
                enforce_detection=False,
                detector_backend='opencv'
            )[0]['embedding']

            return np.array(embedding)
        except Exception as e:
            print(f"Error generating embedding from array: {e}")
            return None

    def compare_embeddings(self, embedding1, embedding2):
        """
        Compare two facial embeddings using cosine similarity

        Args:
            embedding1 (numpy.ndarray): First face embedding
            embedding2 (numpy.ndarray): Second face embedding

        Returns:
            float: Cosine similarity score (0-1, higher is more similar)
        """
        try:
            if embedding1 is None or embedding2 is None:
                return 0.0

            # Ensure embeddings are numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)

            # Calculate cosine similarity
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # Ensure similarity is between 0 and 1
            return max(0.0, min(1.0, similarity))

        except Exception as e:
            print(f"Error comparing embeddings: {e}")
            return 0.0

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points on Earth using Haversine formula

        Args:
            lat1, lon1: Latitude and longitude of first point in decimal degrees
            lat2, lon2: Latitude and longitude of second point in decimal degrees

        Returns:
            float: Distance in kilometers
        """
        try:
            # Convert decimal degrees to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2) ** 2
            c = 2 * math.asin(math.sqrt(a))

            # Radius of earth in kilometers
            r = 6371
            return c * r
        except Exception as e:
            print(f"Error calculating haversine distance: {e}")
            return float('inf')

    def find_top_matches(self, query_embedding, database_embeddings, top_k=3, threshold=0.6,
                         query_lat=None, query_lon=None, max_distance_km=200):
        """
        Find top K matches for a query embedding with optional geographic filtering

        Args:
            query_embedding (numpy.ndarray): Query face embedding
            database_embeddings (list): List of dicts with 'embedding', 'id', 'lat', 'lon' keys
            top_k (int): Number of top matches to return
            threshold (float): Minimum similarity threshold
            query_lat (float): Query latitude for geographic filtering
            query_lon (float): Query longitude for geographic filtering
            max_distance_km (float): Maximum distance in kilometers for geographic filtering

        Returns:
            list: List of matches sorted by similarity (highest first)
        """
        try:
            if query_embedding is None:
                return []

            matches = []

            for item in database_embeddings:
                if 'embedding' in item and item['embedding'] is not None:
                    # Check geographic distance if coordinates are provided
                    if query_lat is not None and query_lon is not None:
                        item_lat = item.get('lat')
                        item_lon = item.get('lon')

                        # Skip if item doesn't have coordinates
                        if item_lat is None or item_lon is None:
                            continue

                        # Calculate distance
                        distance = self.haversine_distance(query_lat, query_lon, item_lat, item_lon)

                        # Skip if distance exceeds maximum
                        if distance > max_distance_km:
                            continue

                    # Calculate facial similarity
                    similarity = self.compare_embeddings(query_embedding, item['embedding'])

                    if similarity >= threshold:
                        match = {
                            'id': item.get('id'),
                            'similarity': float(similarity),
                            'data': item.get('data', {}),
                            'distance_km': self.haversine_distance(
                                query_lat,
                                query_lon,
                                item.get('lat'),
                                item.get('lon'),
                            )
                            if query_lat and query_lon and item.get('lat') and item.get('lon')
                            else None,
                        }
                        matches.append(match)

            # Sort by similarity (highest first) and return top K
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            return matches[:top_k]

        except Exception as e:
            print(f"Error finding matches: {e}")
            return []

    def detect_face(self, image_path):
        """
        Detect if a face is present in the image

        Args:
            image_path (str): Path to the image file

        Returns:
            bool: True if face detected, False otherwise
        """
        try:
            if DeepFace is None:
                print("[facial_recognition] DeepFace unavailable, cannot detect face.")
                return False
            if not os.path.exists(image_path):
                return False

            # Use DeepFace to detect face
            result = DeepFace.extract_faces(  # type: ignore[operator]
                img_path=image_path,
                detector_backend='opencv',
                enforce_detection=False,
            )

            return len(result) > 0

        except Exception as e:
            print(f"Error detecting face: {e}")
            return False

    def extract_faces_from_frame(self, frame):
        """
        Extract faces from a single video frame using DeepFace.

        Args:
            frame (numpy.ndarray): BGR image as returned by OpenCV

        Returns:
            list: List of dicts from DeepFace.extract_faces (each has 'face', 'facial_area', ...)
        """
        try:
            if DeepFace is None:
                print("[facial_recognition] DeepFace unavailable, cannot extract faces from frame.")
                return []
            if frame is None:
                return []

            # Convert BGR (OpenCV) to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            faces = DeepFace.extract_faces(  # type: ignore[operator]
                img_path=rgb_frame,
                detector_backend='opencv',
                enforce_detection=False,
            )
            return faces or []
        except Exception as e:
            print(f"Error extracting faces from frame: {e}")
            return []

    def preprocess_image(self, image_path, output_size=(224, 224)):
        """
        Preprocess image for better face detection

        Args:
            image_path (str): Path to input image
            output_size (tuple): Desired output size (width, height)

        Returns:
            str: Path to preprocessed image or None if failed
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return None

            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Resize if needed
            if image_rgb.shape[:2] != output_size:
                image_rgb = cv2.resize(image_rgb, output_size)

            # Save preprocessed image
            preprocessed_path = image_path.replace('.jpg', '_preprocessed.jpg')
            cv2.imwrite(preprocessed_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))

            return preprocessed_path

        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None


# Global instance
facial_recognition = FacialRecognition()
