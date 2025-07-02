# === PART 1: Imports and Initialization ===
import cv2
import torch
import numpy as np
import time
import pyttsx3
import random
import threading
from collections import defaultdict, Counter
import speech_recognition as sr
import qrcode
from deepface import DeepFace
import os
import pygame

# Initialize voice engine
engine = pyttsx3.init()
def speak(text):
    threading.Thread(target=lambda: engine.say(text) or engine.runAndWait()).start()

# Load YOLOv5
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.conf = 0.5  # Confidence threshold

# Prices and Product Metadata
ITEM_PRICES = {
    'bottle': 20, 'cell phone': 300, 'laptop': 1000,
    'clock': 150, 'teddy bear': 250, 'book': 100,
    'chips': 50, 'cup': 40, 'remote': 60
}

HOT_DEALS = {
    'chips': 'Buy 1 Get 1 Free!',
    'bottle': '20% off today!',
    'teddy bear': 'Special discount for kids!',
    'laptop': 'Flat ₹500 off for students!'
}

SUGGESTIONS = {
    'laptop': ['mouse', 'keyboard'],
    'chips': ['cola', 'cookies'],
    'bottle': ['cup', 'juice'],
    'book': ['pen', 'marker']
}

EMOTION_SUGGESTIONS = {
    'happy': 'You seem happy! How about some chocolates?',
    'sad': 'Maybe a teddy bear will cheer you up.',
    'angry': 'A calming book could help you relax.',
    'surprise': 'Try out our new tech gadgets!',
    'neutral': 'Explore the store freely. Ask for hot deals!',
    'fear': 'Everything’s safe here. Want a cup of coffee?'
}

# Initialize cart and tracking structures
cart = Counter()
last_seen = defaultdict(lambda: time.time())
detection_timers = {}
emotion = "neutral"
frame_count = 0
prev_frame_time = time.time()

# === Beep Sound Fallback ===
pygame.mixer.init()
beep_available = True
try:
    pygame.mixer.music.load("beep.mp3")
except:
    beep_available = False
    print("⚠️ beep.mp3 not found. Beep sound disabled.")

def play_beep():
    if beep_available:
        pygame.mixer.music.play()

# === PART 2: Utility Functions ===
def calculate_total(cart):
    return sum(ITEM_PRICES.get(item, 0) * count for item, count in cart.items())

def generate_qr(cart):
    data = "\n".join([f"{item}: {count} x ₹{ITEM_PRICES.get(item, 0)}" for item, count in cart.items()])
    total = calculate_total(cart)
    qr = qrcode.make(f"Smart Trolley Checkout:\n{data}\nTotal: ₹{total}\nPay at counter or scan UPI.")
    qr.save("checkout_qr.png")

def detect_emotion(frame):
    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        return result[0]['dominant_emotion']
    except:
        return "neutral"

def show_fake_map(suggestions):
    canvas = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(canvas, "Store Map", (200, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    y = 100
    for item in suggestions:
        cv2.putText(canvas, f"{item}", (100, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        y += 40
    cv2.imshow("Fake Store Map", canvas)

def show_hot_deals():
    canvas = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(canvas, "🔥 HOT DEALS TODAY 🔥", (100, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 100, 255), 2)
    y = 100
    for item, deal in HOT_DEALS.items():
        cv2.putText(canvas, f"{item.title()}: {deal}", (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        y += 40
    cv2.imshow("Hot Deals", canvas)

def draw_cart_ui(frame, cart, emotion):
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 160), (30, 30, 30), -1)

    total = calculate_total(cart)
    y_offset = 30
    for i, (item, count) in enumerate(cart.items()):
        price = ITEM_PRICES.get(item, 0)
        text = f"{item}: {count} x ₹{price}"
        cv2.putText(overlay, text, (10, y_offset + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.putText(overlay, f"Total: ₹{total}", (10, y_offset + len(cart) * 25 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(overlay, f"Emotion: {emotion}", (w - 250, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    return cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)

def process_command(command):
    command = command.lower()
    if "total" in command:
        speak(f"Your total is ₹{calculate_total(cart)}")
    elif "suggest" in command:
        for item in cart:
            if item in SUGGESTIONS:
                suggest = ', '.join(SUGGESTIONS[item])
                speak(f"Since you have {item}, you might like {suggest}")
                return
        speak("No suggestions available right now.")
    elif "deals" in command or "hot" in command:
        show_hot_deals()
        speak("Here are today’s hot deals!")
    elif "map" in command:
        sample = random.sample(list(ITEM_PRICES.keys()), 4)
        show_fake_map(sample)
        speak("Here's a map showing item locations.")
    elif "checkout" in command or "pay" in command:
        generate_qr(cart)
        speak("Generating QR code for payment.")
        if os.path.exists("checkout_qr.png"):
            qr_img = cv2.imread("checkout_qr.png")
            cv2.imshow("Scan to Pay", qr_img)
        else:
            speak("Sorry, QR code image not found.")
    elif "thank" in command:
        speak("You're welcome! Happy shopping!")

def voice_assistant():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening for your command.")
        try:
            audio = r.listen(source, timeout=4)
            command = r.recognize_google(audio)
            print("Command:", command)
            process_command(command)
        except:
            speak("Sorry, I didn’t catch that.")

# === PART 3: Real-Time Detection Loop ===
cap = cv2.VideoCapture('0')  # <-- replace with your IP

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (1280, 720))
    detections = model(frame)
    results = detections.pandas().xyxy[0]

    current_items = []
    for _, row in results.iterrows():
        label = row['name']
        conf = row['confidence']
        if conf > 0.5 and label in ITEM_PRICES:
            current_items.append(label)

    if frame_count % 60 == 0:
        emotion = detect_emotion(frame)
    frame_count += 1

    for item in current_items:
        if item not in detection_timers:
            detection_timers[item] = time.time()
        elif time.time() - detection_timers[item] >= 2:
            cart[item] += 1
            last_seen[item] = time.time()
            detection_timers[item] = time.time() + 5

    for item in list(cart.keys()):
        if time.time() - last_seen[item] > 5:
            if cart[item] > 0:
                cart[item] -= 1
                last_seen[item] = time.time()
                threading.Thread(target=play_beep).start()

    # Gesture-based checkout
    people = [row for _, row in results.iterrows() if row['name'] == 'person']
    if len(people) >= 2:
        generate_qr(cart)
        speak("Detected checkout gesture. Here is your QR code.")
        if os.path.exists("checkout_qr.png"):
            qr_img = cv2.imread("checkout_qr.png")
            cv2.imshow("Scan to Pay", qr_img)

    for _, row in results.iterrows():
        if row['confidence'] < 0.5: continue
        label = row['name']
        x1, y1, x2, y2 = map(int, [row['xmin'], row['ymin'], row['xmax'], row['ymax']])
        color = (0, 255, 0) if label in ITEM_PRICES else (100, 100, 100)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    frame = draw_cart_ui(frame, cart, emotion)
    fps = int(1.0 / (time.time() - prev_frame_time))
    prev_frame_time = time.time()
    cv2.putText(frame, f"FPS: {fps}", (1100, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Smart Trolley", frame)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord('r'):
        cart.clear()
        speak("Cart reset.")
    elif key == ord('v'):
        voice_assistant()
    elif key == ord('m'):
        show_fake_map(random.sample(list(ITEM_PRICES.keys()), 4))
    elif key == ord('d'):
        show_hot_deals()
    elif key == ord('c'):
        generate_qr(cart)
        speak("QR Code generated for checkout.")
        if os.path.exists("checkout_qr.png"):
            qr_img = cv2.imread("checkout_qr.png")
            cv2.imshow("Scan to Pay", qr_img)

cap.release()
cv2.destroyAllWindows()

# === PART 4: Greeting ===
speak("Welcome to Smart Trolley! You can ask me to show deals, map, or checkout anytime.")
