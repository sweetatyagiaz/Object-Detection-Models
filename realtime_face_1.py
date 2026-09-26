import os
# Force stable X11 graphics layer compatibility at initialization (Fixes Wayland SegFaults)
os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2
import time
from multiprocessing import Process, Queue, Manager, Event
from deepface import DeepFace

# 1. Global Configurations
DATABASE_DIR = "/home/rakesh/GitRepo/Object-Detection-Models/database/"
DISTANCE_THRESHOLD = 0.60
OPTIMAL_BACKEND = "yunet"  # High-speed CPU optimized detector backend

def recognition_worker(frame_queue, shared_dict, stop_event):
    """
    Dedicated AI core process. Runs on a separate CPU core, pulls frames 
    asynchronously from the queue, runs inference, and writes results back.
    """
    print(f"🧠 DeepFace Parallel Inference Engine Active (Using {OPTIMAL_BACKEND}).")
    
    while not stop_event.is_set():
        try:
            # Grab frame with a timeout so the block can un-gate safely if stop event is set
            frame_to_process = frame_queue.get(timeout=1.0)
        except Exception:
            continue
            
        try:
            results = DeepFace.find(
                img_path=frame_to_process, 
                db_path=DATABASE_DIR,
                model_name="Facenet512",
                detector_backend=OPTIMAL_BACKEND,
                enforce_detection=False,
                silent=True
            )
            
            df = results if isinstance(results, list) else [results]
            df = df[0] if len(df) > 0 else None

            if df is not None and not df.empty:
                valid_matches = df[df['distance'] < DISTANCE_THRESHOLD]
                
                # Pull coordinates safely via .loc using row 0
                x = int(df.loc[0, 'source_x'])
                y = int(df.loc[0, 'source_y'])
                w = int(df.loc[0, 'source_w'])
                h = int(df.loc[0, 'source_h'])
                
                if not valid_matches.empty:
                    best_match = valid_matches.sort_values(by='distance', ascending=True).iloc[0]
                    person_name = os.path.basename(os.path.dirname(best_match['identity']))
                    confidence = best_match['confidence']
                    label = f"{person_name} ({confidence:.1f}%)"
                    color = (0, 255, 0)  # Green for match
                else:
                    label = "Unknown Person"
                    color = (0, 0, 255)  # Red for unknown
                    
                # Write back coordinates to safe shared process dictionary memory
                shared_dict["latest"] = {"box": (x, y, w, h), "label": label, "color": color}
            else:
                shared_dict["latest"] = None
                
        except Exception as e:
            # Suppress tracking exceptions to preserve visual performance
            pass

# --- Main Runtime Orchestration Hub ---
if __name__ == '__main__':
    # Initialize thread-safe shared inter-process data management elements
    manager = Manager()
    shared_dict = manager.dict()
    shared_dict["latest"] = None
    
    # Restrict queue depth to 1 to enforce an asynchronous frame-dropping strategy
    frame_queue = Queue(maxsize=1)
    stop_event = Event()
    
    # 2. Spawn and start the AI engine process on a separate CPU core
    ai_process = Process(target=recognition_worker, args=(frame_queue, shared_dict, stop_event), daemon=True)
    ai_process.start()
    
    # 3. Initialize Webcam Capture locally within the main rendering process
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Clear camera pipeline frame backlogs
    time.sleep(0.5)  # Give the device sensor 500ms to claim the hardware slot securely
    
    if not cap.isOpened():
        print("❌ Error: Could not reach webcam interface hardware layer.")
        exit()
        
    print("🎥 Zero-Lag Multiprocessing Feed Active. Press 'q' to safely exit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Asynchronous frame delivery: If the AI process core is idle, give it a frame
        if frame_queue.empty():
            try:
                frame_queue.put_nowait(frame.copy())
            except Exception:
                pass
                
        # 4. Read latest detection metrics from the shared process buffer dictionary
        latest_recognition = shared_dict["latest"]
        if latest_recognition is not None:
            x, y, w, h = latest_recognition["box"]
            lbl = latest_recognition["label"]
            clr = latest_recognition["color"]
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), clr, 2)
            cv2.putText(frame, lbl, (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.6, clr, 1, cv2.LINE_AA)
            
        # Display the live window layout frame at the hardware's native max FPS rate
        cv2.imshow("Parallel Multi-Core Zero-Lag Feed", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # 5. Clean teardown across the multi-process cluster
    print("\n🛑 Shutting down backend processes cleanly...")
    stop_event.set()
    ai_process.terminate()
    ai_process.join()
    
    cap.release()
    cv2.destroyAllWindows()
    print("🎥 System closed successfully.")