import cv2
import torch
import time
import random
import pyttsx3
import speech_recognition as sr

# Load YOLOv5
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', verbose=False)

# Product prices
product_prices = {
    "teddy bear": 20,
    "laptop": 1000,
    "chips": 10,
    "colddrink": 15,
    "bottle": 12,
    "clock": 30,
    "chocolate": 5,
    "mobile phone": 800,
}

cart = {}
last_seen = {}
removed_time = {}

# Camera settings
IP_CAM_URL = "http://192.168.137.135:8080/video"
FALLBACK_CAM_INDEX = 0

# Voice setup
engine = pyttsx3.init()
r = sr.Recognizer()

def speak(text):
    print("[Assistant]:", text)
    engine.say(text)
    engine.runAndWait()

def get_video_capture():
    print("[INFO] Trying IP camera...")
    cap = cv2.VideoCapture(IP_CAM_URL)
    time.sleep(2)
    ret, frame = cap.read()
    if ret:
        print("[SUCCESS] IP camera connected.")
        return cap
    else:
        print("[FAILED] Switching to webcam.")
        cap = cv2.VideoCapture(FALLBACK_CAM_INDEX)
        time.sleep(2)
        ret, frame = cap.read()
        if ret:
            print("[SUCCESS] Webcam connected.")
            return cap
        else:
            print("[ERROR] No camera available.")
            return None

def update_cart(item):
    cart[item] = cart.get(item, 0) + 1
    speak(f"{item} added to cart")

def remove_item(item):
    if item in cart:
        cart[item] -= 1
        if cart[item] <= 0:
            del cart[item]
        speak(f"{item} removed from cart")

def display_cart(frame):
    y = 30
    total = 0
    for item, qty in cart.items():
        price = product_prices.get(item, 0)
        total += price * qty
        line = f"{item} x{qty} = ₹{price * qty}"
        cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        y += 25
    cv2.putText(frame, f"Total: ₹{total}", (10, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

def run_detection(frame):
    global last_seen, removed_time
    results = model(frame)
    detections = results.pandas().xyxy[0]
    current = set()

    for _, row in detections.iterrows():
        label = row['name']
        if label in product_prices:
            current.add(label)
            x1, y1, x2, y2 = map(int, [row['xmin'], row['ymin'], row['xmax'], row['ymax']])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            now = time.time()
            if label not in last_seen:
                last_seen[label] = now
            elif now - last_seen[label] >= 2:
                update_cart(label)
                last_seen[label] = now  # reset to avoid repeated addition

    # Handle disappearance
    now = time.time()
    for label in list(last_seen.keys()):
        if label not in current:
            if label not in removed_time:
                removed_time[label] = now
            elif now - removed_time[label] >= 3:
                remove_item(label)
                removed_time.pop(label)
                last_seen.pop(label)
        else:
            removed_time[label] = now  # Reset removal timer

    display_cart(frame)

# ------------------ MAIN ------------------
speak("Welcome to Smart Trolley!")
cap = get_video_capture()

if cap is None:
    speak("Sorry, no camera available.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to read frame.")
        break

    run_detection(frame)
    cv2.imshow("Smart Trolley", frame)
    key = cv2.waitKey(1)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
speak("Thank you for using Smart Trolley!")
