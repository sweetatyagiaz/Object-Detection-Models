
# yolo track model=yolo26n.pt source="../Datasets/input_video.mp4" tracker="bytetrack.yaml" show=True

import cv2
from ultralytics import YOLO

model = YOLO("yolo26n.pt")
# cap = cv2.VideoCapture("../Datasets/input_video.mp4")
cap = cv2.VideoCapture("../Datasets/recorded_cam.mp4")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Run ByteTrack on the current frame stream
    # persist=True ensures the tracker remembers IDs across consecutive frames
    results = model.track(frame, tracker="bytetrack.yaml", persist=True)

    # Process tracking outputs
    boxes = results[0].boxes.xyxy.cpu().numpy()     # Bounding box coordinates
    
    if results[0].boxes.id is not None:
        track_ids = results[0].boxes.id.cpu().tolist() # Unique persistent object IDs
        class_ids = results[0].boxes.cls.cpu().tolist() # Detected class indexes
        
        for box, track_id, class_id in zip(boxes, track_ids, class_ids):
            x1, y1, x2, y2 = map(int, box)
            label = f"ID: {int(track_id)} | Class: {int(class_id)}"
            
            # Draw standard tracking visualization via OpenCV
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("YOLO26 + ByteTrack Pipeline", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
