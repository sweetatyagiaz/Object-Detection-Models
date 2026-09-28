
import os
import glob
import cv2
import numpy as np
import shutil


def delete_blank_image(EDGE_THRESHOLD = 0.8, SAFE_MODE = True, img_folder_path=False, trash_folder="deleted_blank_images/"):
    # --- CONFIGURATION ---
    # TARGET_FOLDER = "dataset_raw/person_1"  # Path to your folder with multiple images
    # EDGE_THRESHOLD = 0.8                   # Lower = more strict (keeps almost everything)
                                        # Higher = aggressive (deletes low-detail frames)

    # (Optional) Set to True to move files to a trash folder instead of deleting permanently
    # SAFE_MODE = True  
    # trash_folder = "deleted_blank_images/"

    if SAFE_MODE:
        os.makedirs(trash_folder, exist_ok=True)

    # List all files in the target directory
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    all_files = [f for f in os.listdir(img_folder_path) if f.lower().endswith(image_extensions)]

    print(f"Scanning {len(all_files)} images in '{img_folder_path}'...")

    blank_count = 0
    for file_name in all_files:
        file_path = os.path.join(img_folder_path, file_name)
        
        # 1. Load image in grayscale
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"Skipping unreadable file: {file_name}")
            continue
            
        # 2. Smooth out image sensor noise
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        
        # 3. Detect edges and structures
        edges = cv2.Canny(blurred, 30, 100)
        
        # 4. Calculate the percentage of structural edges in the frame
        total_pixels = edges.size
        edge_pixels = cv2.countNonZero(edges)
        edge_percentage = (edge_pixels / total_pixels) * 100
        
        # 5. Filter and handle blank files
        if edge_percentage < EDGE_THRESHOLD:
            blank_count += 1
            if SAFE_MODE:
                print(f"[BLANK] Moving {file_name} to trash (Edge Density: {edge_percentage:.3f}%)")
                shutil.move(file_path, os.path.join(trash_folder, file_name))
            else:
                print(f"[BLANK] Deleting {file_name} (Edge Density: {edge_percentage:.3f}%)")
                os.remove(file_path)

    print("\n--- CLEANUP COMPLETE ---")
    print(f"Total images scanned: {len(all_files)}")
    print(f"Blank images removed: {blank_count}")
    if SAFE_MODE and blank_count > 0:
        print(f"Review deleted images in: '{trash_folder}'")

    return True

def files_from_folder(dataset_path = False, file_extension='jpg'):    
    # The '**/*.jpg' means look through ALL subfolders for any .jpg file
    subfolder_pattern = os.path.join(dataset_path, "**", "*."+file_extension.replace('.', ''))
    all_subfolder_images = glob.glob(subfolder_pattern, recursive=True)

    print(f"Found {len(all_subfolder_images)} images across all subfolders.")
    for file_path in all_subfolder_images:
        print(file_path)

    return all_subfolder_images

def extract_images(frame_interval = 10, saved_count=0, video_path = False, output_folder = False):
    # --- CONFIGURATION ---
    #video_path = "/home/rakesh/Downloads/Maternity Shoot/13 dec vimla tyagi.mp4"   # Path to your recorded video
    # video_path = "/home/rakesh/Downloads/Data/Dataset Video/person_1_webcam.mp4"   # Path to your recorded video
    # output_folder = "dataset_raw/person_2" # Where to save the extracted images
    # frame_interval = 10                     # Save every 10th frame (keeps data unique)

    if not video_path:
        print('error-enter video path')
        return False
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    # saved_count = file_count

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break # End of video
        
        # Only save at the specified interval
        if frame_count % frame_interval == 0:
            img_name = f"person1_frame_{saved_count:04d}.jpg"
            img_path = os.path.join(output_folder, img_name)
            cv2.imwrite(img_path, frame)
            saved_count += 1
            
        frame_count += 1

    cap.release()
    print(f"Successfully extracted {saved_count} diverse images to {output_folder}!")

    # Delete bank images
    delete_blank_image(SAFE_MODE=False, img_folder_path=output_folder)

    return saved_count