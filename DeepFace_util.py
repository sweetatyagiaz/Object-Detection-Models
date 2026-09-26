import os
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def multi_face_dashboard(DISTANCE_THRESHOLD=0.6, QUERY_IMAGE=False, results=False):
    # Load Background Image
    img = cv2.imread(QUERY_IMAGE)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    fig, ax = plt.subplots(figsize=(14, 9))
    ax.imshow(img_rgb)

    # 4. Loop Over Each Detected Face Frame
    for face_idx, df in enumerate(results):
        if df.empty:
            continue
            
        # FIX: Use .loc[0, 'column_name'] to avoid the TypeError
        x = df.loc[0, 'source_x']
        y = df.loc[0, 'source_y']
        w = df.loc[0, 'source_w']
        h = df.loc[0, 'source_h']
        
        # Filter matches based on the threshold
        valid_matches = df[df['distance'] < DISTANCE_THRESHOLD]
        
        if not valid_matches.empty:
            # Sort to grab the best structural match record
            sorted_matches = valid_matches.sort_values(by='distance', ascending=True)
            
            # FIX: Use .iloc[0] to grab the first row object safely
            best_match = sorted_matches.iloc[0]
            best_match_path = best_match['identity']
            confidence = best_match['confidence']
            distance = best_match['distance']
            
            person_name = os.path.basename(os.path.dirname(best_match_path))
            filename = os.path.basename(best_match_path)
            
            label_text = f"ID: {person_name}\nConf: {confidence:.1f}%\nDist: {distance:.3f}\nFile: {filename}"
            box_color = '#00FF00'  # Bright Neon Green for matched
        else:
            label_text = f"Face #{face_idx + 1}\nUnknown\nNo Match Found"
            box_color = '#FF0000'  # Bright Red for Unmatched
            
        # Render Bounding Box Patch
        rect = patches.Rectangle((x, y), w, h, linewidth=2.5, edgecolor=box_color, facecolor='none')
        ax.add_patch(rect)
        
        # Overlay Multi-Line Metadata Details Box
        ax.text(
            x, y - 12, label_text, 
            color='white', fontweight='bold', fontsize=8,
            bbox=dict(facecolor=box_color, alpha=0.8, edgecolor='none', boxstyle='round,pad=0.4')
        )

    ax.axis('off')
    plt.title(f"Facial Verification Dashboard Matrix\n[ Green = Matched Below {DISTANCE_THRESHOLD} | Red = Not Matched ]", fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.show()