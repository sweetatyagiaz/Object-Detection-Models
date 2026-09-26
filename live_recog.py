import os

# Force the system GUI to hook into the highly stable X11 compatibility layer
os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2
import queue
import threading
from deepface import DeepFace

# 1. Configuration
DATABASE_DIR = "/home/rakesh/GitRepo/Object-Detection-Models/database/"
DISTANCE_THRESHOLD = 0.60

# Thread-safe queues to drop historical frames and keep stream running live
frame_queue = queue.Queue(maxsize=1)
latest_recognition = None

def recognition_worker():
    """
    Dedicated worker thread. Processes frames using the fast yolov8 backend 
    to bypass the broken OpenCV/MediaPipe dependency bugs.
    """
    global latest_recognition
    print("🧠 DeepFace AI Processing Thread Active (Using YOLOv8).")
    
    while True:
        # Blocks until a fresh frame arrives from the webcam capture loop
        frame_to_process = frame_queue.get()
        
        try:
            # YOLOv8 isolates bounding face coordinates rapidly in a live environment
            results = DeepFace.find(
                img_path=frame_to_process, 
                db_path=DATABASE_DIR,
                model_name="Facenet512",
                detector_backend="yunet",  # High-speed alternative detector
                enforce_detection=False,
                silent=True
            )
            
            df = results if isinstance(results, list) else [results]
            df = df[0] if len(df) > 0 else None

            if df is not None and not df.empty:
                valid_matches = df[df['distance'] < DISTANCE_THRESHOLD]
                
                # Fetch spatial parameters using .loc to prevent TypeErrors
                x = int(df.loc[0, 'source_x'])
                y = int(df.loc[0, 'source_y'])
                w = int(df.loc[0, 'source_w'])
                h = int(df.loc[0, 'source_h'])
                
                if not valid_matches.empty:
                    best_match = valid_matches.sort_values(by='distance', ascending=True).iloc[0]
                    person_name = os.path.basename(os.path.dirname(best_match['identity']))
                    confidence = best_match['confidence']
                    label = f"{person_name} ({confidence:.1f}%)"
                    color = (0, 255, 0)  # Green for known match
                else:
                    label = "Unknown Person"
                    color = (0, 0, 255)  # Red for unknown alert
                    
                latest_recognition = {"box": (x, y, w, h), "label": label, "color": color}
            else:
                latest_recognition = None
                
        except Exception as e:
            print(f"DeepFace worker warning: {e}")
            
        frame_queue.task_done()

# Start background AI processor thread
threading.Thread(target=recognition_worker, daemon=True).start()

# Initialize Webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Clear OS hardware buffer stack lag

if not cap.isOpened():
    print("❌ Error: Could not reach webcam interface frame.")
    exit()

print("🎥 Real-time stream running at max hardware capacity. Press 'q' to close.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Asynchronous Frame Dropping Strategy
    if frame_queue.empty():
        try:
            frame_queue.put_nowait(frame.copy())
        except queue.Full:
            pass

    # Draw the latest tracking markers over the UI if they exist
    if latest_recognition is not None:
        x, y, w, h = latest_recognition["box"]
        lbl = latest_recognition["label"]
        clr = latest_recognition["color"]
        
        cv2.rectangle(frame, (x, y), (x + w, y + h), clr, 2)
        cv2.putText(frame, lbl, (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.6, clr, 1, cv2.LINE_AA)

    # Render directly to the screen window
    cv2.imshow("Zero-Lag Face Verification Feed", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("🎥 Framework shutdown clean.")
