import cv2

# Open the default camera (index 0)
cap = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Get frame width and height from the camera
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define the codec and create a VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('Datasets/recorded_cam.mp4', fourcc, 20.0, (frame_width, frame_height))

print("Recording... Press 'q' to stop.")

while True:
    # Read frame by frame
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Failed to grab frame.")
        break

    # Write the frame to the output file
    out.write(frame)

    # Display the live frame
    cv2.imshow('Live Camera Feed', frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release everything once finished
cap.release()
out.release()
cv2.destroyAllWindows()
print("Recording saved as recorded_cam.mp4")