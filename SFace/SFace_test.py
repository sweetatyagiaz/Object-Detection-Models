import os
import glob
import cv2
import numpy as np
from SFace_utils import initialize_model, load_face_templates, identify_face_from_memory, extract_all_faces, files_from_folder, \
                        ideentify_faces

# Set path
recognizer_model_path = '../Datasets/face_recognition_sface_2021dec.onnx'
detector_model_path = '../Datasets/face_detection_yunet_2023mar.onnx'
output_folder = '../Datasets/extracted_faces'
test_img_path = '../Datasets/group_photo.jpg'
dataset_dir = '../database'

input_size=(0, 0) 
score_threshold=0.45
nms_threshold=0.3

# Initlize Model
detector_model, recognizer_model = initialize_model(detector_model_path=detector_model_path, 
                                                    recognizer_model_path=recognizer_model_path, 
                                                    input_size=input_size, score_threshold=score_threshold, 
                                                    nms_threshold=nms_threshold)

# 1. Load the dataset from directory at runtime
face_database_dict = load_face_templates(detector_model=detector_model, recognizer_model=recognizer_model, dataset_dir=dataset_dir)

# 2. Test identification
identify_face_from_memory(detector_model=detector_model, recognizer_model=recognizer_model, 
                          query_img_path="../Datasets/vimala.jpg", templates=face_database_dict)


# Test Multipple Files
test_images = ['Tejrit.jpg', 'Shrinav.jpg', 'vimala.jpg', 'obama.jpg', 'group_photo.jpg']

for idx in test_images:
    # identify_face_from_memory("Datasets/"+idx, face_database_dict)
    identify_face_from_memory(detector_model=detector_model, recognizer_model=recognizer_model, 
                          query_img_path="../Datasets/"+idx, templates=face_database_dict)


# Extract all face from images
extract_all_faces(image_path=test_img_path, recognizer_model=recognizer_model, 
                  detector_model=detector_model, output_folder=output_folder, score_threshold=0.3)

# Read all extracted files
# file_list = files_from_folder(dataset_path='Datasets/extracted_faces/')
file_list = files_from_folder(dataset_path=output_folder)

# Identify faces
ideentify_faces(detector_model=detector_model, recognizer_model=recognizer_model, face_database_dict=face_database_dict, 
                images_list=file_list)