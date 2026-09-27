import cv2
import numpy as np
from insightface.app import FaceAnalysis

def get_face_embedding(image_path, app):
    """Reads an image and returns the ArcFace embedding vector for the first detected face."""
    # Load image using OpenCV
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image from path: {image_path}")
    
    # Detect faces and extract features
    faces = app.get(img)
    
    if len(faces) == 0:
        raise ValueError(f"No face detected in image: {image_path}")
    
    # Return the 512-dimensional embedding of the first detected face
    return faces[0].normed_embedding

def verify_faces(img1_path, img2_path, threshold=0.45):
    """Compares two face embeddings using Cosine Similarity."""
    # Initialize the InsightFace application
    # 'buffalo_l' is the accuracy-focused model pack containing RetinaFace and ArcFace
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    try:
        # Extract 512-D embeddings
        embedding1 = get_face_embedding(img1_path, app)
        embedding2 = get_face_embedding(img2_path, app)
        
        # Calculate Cosine Similarity: (A . B) / (||A|| * ||B||)
        # Because they are already normalized by InsightFace, a simple dot product suffices
        similarity = np.dot(embedding1, embedding2)
        
        print(f"\n--- Verification Results ---")
        print(f"Cosine Similarity Score: {similarity:.4f}")
        
        if similarity >= threshold:
            print(" Result: MATCH (Same person)")
            return True
        else:
            print(" Result: MISMATCH (Different people)")
            return False
            
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

# --- Example Usage ---
if __name__ == "__main__":
    # Replace these with the paths to your local images
    image_a = "../Datasets/person1_photo1.jpg"
    image_b = "../Datasets/person1_photo2.jpg"
    
    # A standard threshold for the 'buffalo_l' ArcFace model is usually between 0.40 and 0.50
    verify_faces(image_a, image_b, threshold=0.45)
