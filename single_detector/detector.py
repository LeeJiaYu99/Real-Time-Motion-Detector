import cv2
import keyboard
import sys

sys.path.insert(0, r"..\motion_detector\utils")
from detector_utils import detect_motion

def main(display=True):
    # Open stream
    cap = cv2.VideoCapture(0)
    ret, frame1 = cap.read()

    while True:
        ret, frame2 = cap.read()
        if not ret:
            break
        
        # Detect motion
        merged_boxes = detect_motion(frame1, frame2)
        result_frame = frame2.copy()
        for (x, y, w, h) in merged_boxes:
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)   

        frame1 = frame2

        if display:
            # Show result in video form
            cv2.imshow("Motion Detection", result_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            # Show result in text form
            if len(merged_boxes) > 0:
                print("motion detected")
                if keyboard.is_pressed('q'):
                    print("Exit program...")
                    break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main(display=True)
