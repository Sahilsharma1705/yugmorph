import cv2

for i in range(3):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i} is working")
        ret, frame = cap.read()
        if ret:
            cv2.imshow(f"Camera {i}", frame)
            cv2.waitKey(0)
        cap.release()
    else:
        print(f"Camera {i} not working")

cv2.destroyAllWindows()
