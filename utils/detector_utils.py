import cv2

def compute_iou(box1, box2):
    """
    Compute Intersection over Union (IoU) of two bounding box regions.

    Args:
        box1 (tuple of x, y, w, h): The first bounding box region.
        box2 (tuple of x, y, w, h): The second bounding box region.

    Returns:
        float: Intersection over Union (IoU) between box1 and box2.
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)

    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    if union_area == 0:
        return 0
    return inter_area / union_area

def merge_boxes(boxes, iou_threshold):
    """
    Merge overlapping bounding box into a single bounding box region.

    Args:
        boxes (list of tuple of x, y, w, h): List of bounding box region.
        iou_threshold (float): Threshold for ratio of intersection.

    Returns:
        list of tuple of x, y, w, h: List of bounding box region after the intersect boxes are merged.
    """
    merged = []
    used = [False] * len(boxes)

    for i in range(len(boxes)):
        if used[i]:
            continue
        x, y, w, h = boxes[i]
        for j in range(i + 1, len(boxes)):
            if used[j]:
                continue
            iou = compute_iou(boxes[i], boxes[j])
            if iou > iou_threshold:
                x2, y2, w2, h2 = boxes[j]
                x = min(x, x2)
                y = min(y, y2)
                w = max(x + w, x2 + w2) - x
                h = max(y + h, y2 + h2) - y
                used[j] = True
        merged.append((x, y, w, h))
    return merged

def detect_motion(frame1, frame2):
    """
    Detect motion by comparing two consecutive frames using computation of absolute difference by opencv.

    Args:
        frame1 (numpy ndarray): First frame.
        frame2 (numpy ndarray): Consecutive second frame.

    Returns:
        list of tuple of x, y, w, h: List of bounding box where motion is detected.
    """
    # Turn image to greyscale and apply gaussian blur
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.GaussianBlur(gray1, (9, 9), 0)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.GaussianBlur(gray2, (9, 9), 0)

    # Check absolute difference between two images
    diff = cv2.absdiff(gray1, gray2)
    thresh = cv2.threshold(diff, 3, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Find edges of the pixels left as absolute differences in the image
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw bounding box around the region detected with contour
    boxes = []
    for contour in contours:
        if cv2.contourArea(contour) < 300:
            continue
        (x, y, w, h) = cv2.boundingRect(contour)
        boxes.append((x, y, w, h))

    # Merge overlapping/nearby boxes
    merged_boxes = merge_boxes(boxes, iou_threshold=0.01)

    return merged_boxes