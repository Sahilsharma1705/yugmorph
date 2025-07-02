import cv2
import torch
import time
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import pyttsx3
import speech_recognition as sr
import random

# === CONFIGURATION ===
CUSTOM_MODEL_PATH = "runs/train/exp/weights/best.pt"  # ← update path to your model
IP_CAM_URL = "http://192.168.137.135:8080/video"      # ← your phone IP camera
FALLBACK_CAM_INDEX = 0

product_prices = {
    "chips": 10,
    "colddrink": 15,
    "teddy bear": 20,
    "bottle": 12,
    "clock": 30,
    "chocolate": 5,
    "mobile phone": 800,
    "laptop": 1000,
}

# === SETUP ===
model = torch.hub.load('ultralytics/yolov5', 'custom', path=CUSTOM_MODEL_PATH)
engine = pyttsx3.init()
r = sr.Recognizer()

cart = {}
last_detection_time = {}
last_removed_time = {}

def speak(msg):
    print("[Assistant]:", msg)
    engine.say(msg)
    engine.runAndWait()

def get_video_capture():
    cap = cv2.VideoCapture(IP_CAM_URL)
    time.sleep(2)
    if cap.isOpened():
        print("[INFO] IP Camera connected.")
        return cap
    cap = cv2.VideoCapture(FALLBACK_CAM_INDEX)
    if cap.isOpened():
        print("[INFO] Fallback webcam connected.")
        return cap
    return None

def update_cart(item):
    cart[item] = cart.get(item, 0) + 1
    speak(f"{item} added to cart.")

def remove_item(item):
    if item in cart:
        cart[item] -= 1
        if cart[item] <= 0:
            del cart[item]
        speak(f"{item} removed from cart.")

def display_cart(frame):
    y = 30
    total = 0
    for item, qty in cart.items():
        price = product_prices.get(item, 0)
        total += qty * price
        text = f"{item} x{qty} = ₹{qty*price}"
        cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)
        y += 25
    cv2.putText(frame, f"Total: ₹{total}", (10, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

def show_checkout(frame):
    cv2.putText(frame, "Scan QR to Checkout!", (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)

def suggest_items():
    all_items = list(product_prices.keys())
    suggestions = random.sample(all_items, 3)
    speak("You might also like: " + ", ".join(suggestions))

def listen_command():
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        speak("Listening...")
        try:
            audio = r.listen(source, timeout=4)
            cmd = r.recognize_google(audio).lower()
            print("Heard:", cmd)
            return cmd
        except:
            speak("Sorry, I didn’t catch that.")
            return ""

def handle_voice(cmd):
    if "total" in cmd:
        total = sum(product_prices.get(i, 0) * q for i, q in cart.items())
        speak(f"Your total is ₹{total}")
    elif "suggest" in cmd or "recommend" in cmd:
        suggest_items()
    elif "checkout" in cmd:
        speak("Generating QR code. Please scan to pay.")
        return True
    elif "trending" in cmd:
        speak("Trending items: chips, chocolate, and teddy bear.")
    return False

def run_detection(frame):
    results = model(frame)
    detections = results.pandas().xyxy[0]
    detected_now = []

    for _, row in detections.iterrows():
        label = row['name']
        if label in product_prices:
            x1, y1, x2, y2 = map(int, [row['xmin'], row['ymin'], row['xmax'], row['ymax']])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

            detected_now.append(label)
            now = time.time()
            if label not in last_detection_time:
                last_detection_time[label] = now
            elif now - last_detection_time[label] >= 2:
                update_cart(label)
                last_detection_time[label] = now

    now = time.time()
    for label in list(last_detection_time.keys()):
        if label not in detected_now:
            if label not in last_removed_time:
                last_removed_time[label] = now
            elif now - last_removed_time[label] >= 3:
                remove_item(label)
                del last_detection_time[label]
                del last_removed_time[label]
        else:
            last_removed_time[label] = now

    display_cart(frame)

# === MAIN ===
speak("Welcome to Smart Trolley!")
cap = get_video_capture()

if cap is None:
    speak("No camera available. Please reconnect and restart.")
    exit()

checkout = False
while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Frame not received.")
        break

    run_detection(frame)
    if checkout:
        show_checkout(frame)

    cv2.imshow("Smart Trolley", frame)
    key = cv2.waitKey(1)

    if key == ord('q'):
        break
    elif key == ord('v'):
        cmd = listen_command()
        if handle_voice(cmd):
            checkout = True
    elif key == ord('c'):
        checkout = True
        speak("Checkout started. Please scan the QR.")

cap.release()
cv2.destroyAllWindows()
speak("Thanks for shopping with Smart Trolley!")
