import os
import cv2
import threading
from deepface import DeepFace

# 1. Configuration
DATABASE_DIR = "/home/rakesh/GitRepo/Object-Detection-Models/database/"
DISTANCE_THRESHOLD = 0.60

# Global variables to pass data between the webcam thread and the DeepFace recognition thread
latest_frame = None
recognition_results = []
is_processing = False

def background_recognition(frame_to_process):
    """
    Runs DeepFace search in a background thread using MTCNN to bypass the broken OpenCV classifier.
    """
    global recognition_results, is_processing
    try:
        # SWITCH BACKEND TO 'mtcnn' OR 'mediapipe'
        results = DeepFace.find(
            img_path=frame_to_process, 
            db_path=DATABASE_DIR,
            model_name="Facenet512",
            detector_backend="mtcnn",   # <-- Replaces the bugged "opencv" backend
            enforce_detection=False,
            silent=True
        )
        
        if isinstance(results, list):
            recognition_results = results
        else:
            recognition_results = [results]
            
    except Exception as e:
        print(f"Error in recognition thread: {e}")
    finally:
        is_processing = False


# 2. Initialize Webcam Capture (0 is usually the default built-in webcam)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam.")
    exit()

print("🎥 Webcam started. Press 'q' to exit.")

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame.")
        break

    frame_count += 1
    
    # Trigger the background recognition thread every 10 frames to avoid bottlenecking
    if frame_count % 10 == 0 and not is_processing:
        is_processing = True
        # Send a copy of the current frame to the background thread
        threading.Thread(target=background_recognition, args=(frame.copy(),), daemon=True).start()

    # 3. Draw Bounding Boxes and Labels based on the latest available results
    for df in recognition_results:
        if df.empty:
            continue
            
        # Extract coordinates safely
        try:
            x = int(df.loc[0, 'source_x'])
            y = int(df.loc[0, 'source_y'])
            w = int(df.loc[0, 'source_w'])
            h = int(df.loc[0, 'source_h'])
        except (KeyError, IndexError):
            continue

        # Filter matches based on the threshold
        valid_matches = df[df['distance'] < DISTANCE_THRESHOLD]
        
        if not valid_matches.empty:
            sorted_matches = valid_matches.sort_values(by='distance', ascending=True)
            best_match = sorted_matches.iloc[0]
            
            # Parse identity name
            person_name = os.path.basename(os.path.dirname(best_match['identity']))
            confidence = best_match['confidence']
            distance = best_match['distance']
            
            label_text = f"{person_name} ({confidence:.1f}%)"
            box_color = (0, 255, 0)  # Green in BGR
        else:
            label_text = "Unknown"
            box_color = (0, 0, 255)  # Red in BGR

        # Draw the rectangle box over the face
        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
        
        # Display text background banner for readability
        cv2.putText(
            frame, label_text, (x, y - 10), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2, cv2.LINE_AA
        )

    # 4. Display the live feed window
    cv2.imshow("Real-Time Face Verification Dashboard", frame)

    # Break loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up resources
cap.release()
cv2.destroyAllWindows()
print("🎥 Webcam closed successfully.")
