# === Part 1: Imports and Initialization ===
import os
import cv2
import torch
import time
import numpy as np
import pygame
import pyttsx3
import threading
import speech_recognition as sr
from datetime import datetime
import random

# === ENVIRONMENT CACHE PATHS ===
os.environ['TORCH_HOME'] = 'D:/smart_trolley_data/torch'
os.environ['TRANSFORMERS_CACHE'] = 'D:/smart_trolley_data/transformers'
os.environ['HF_HOME'] = 'D:/smart_trolley_data/huggingface'
os.environ['PYTORCH_TRANSFORMERS_CACHE'] = 'D:/smart_trolley_data/pytorch_transformers'
os.environ['PYTORCH_PRETRAINED_BERT_CACHE'] = 'D:/smart_trolley_data/bert'

# === Load YOLOv5 Model ===
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', force_reload=False)

# === Product Prices ===
item_prices = {
    'teddy bear': 10.99, 'laptop': 999.99, 'cell phone': 599.99,
    'bottle': 1.49, 'book': 15.75, 'cup': 2.99, 'clock': 8.49,
    'backpack': 35.00, 'chips': 3.50, 'chocolate': 2.25,
    'coldrink': 1.25, 'remote': 5.50
}

cart, detection_memory, disappear_memory = {}, {}, {}
previous_purchases = ['teddy bear', 'chocolate']
fun_tips = [
    "✨ Tip: Try scanning slowly for better accuracy.",
    "🍭 Say 'hello' or 'suggest' to interact with the assistant!",
    "🏫 Add a teddy bear to your cart for a surprise!",
    "💬 You can say 'bye' to end the voice assistant."
]

# === Greeting Setup ===
hour = datetime.now().hour
greeting = "🌅 Good Morning!" if hour < 12 else "🌞 Good Afternoon!" if hour < 18 else "🌙 Good Evening!"

# === Pygame UI Setup ===
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Smart Trolley Interface")
font = pygame.font.SysFont("arial", 28)
clock = pygame.time.Clock()

# === TTS Setup ===
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.say(greeting)
engine.runAndWait()

# === Voice Assistant Setup ===
recognizer = sr.Recognizer()
checkout_triggered, animated_total, checkout_message_displayed = False, 0, False

# === Product Icons ===
product_images = {
    'teddy bear': 'icons/teddy.png', 'laptop': 'icons/laptop.png',
    'cell phone': 'icons/phone.png', 'bottle': 'icons/bottle.png',
    'book': 'icons/book.png', 'cup': 'icons/cup.png',
    'clock': 'icons/clock.png', 'backpack': 'icons/bag.png',
    'chips': 'icons/chips.png', 'chocolate': 'icons/choco.png',
    'coldrink': 'icons/coldrink.png', 'remote': 'icons/remote.png'
}

product_icons = {}
for name, path in product_images.items():
    try:
        product_icons[name] = pygame.image.load(path)
    except:
        product_icons[name] = None

# === NLP Voice Response ===
def simple_response(command):
    global checkout_triggered
    command = command.lower()
    if "hello" in command or "hi" in command:
        return "Hello! I'm your smart trolley assistant."
    elif "how are you" in command:
        return "I'm doing great, ready to help you shop!"
    elif "suggest" in command or "cool" in command:
        return "Try some chocolates or a cold drink – they're trending today!"
    elif "sale" in command or "discount" in command:
        return "Yes! Great sale on chips and teddy bears today!"
    elif "checkout" in command:
        checkout_triggered = True
        return "Proceeding to checkout. Please wait."
    elif "bye" in command:
        return "Goodbye! Happy shopping!"
    elif "total" in command:
        total = sum(item_prices[label] * count for label, count in cart.items())
        return f"Your total is ${total:.2f}"
    elif "most expensive" in command:
        if cart:
            max_item = max(cart.items(), key=lambda x: item_prices[x[0]] * x[1])[0]
            return f"The most expensive item is {max_item}."
        else:
            return "Your cart is empty!"
    elif "trending" in command:
        return "Trending items: chips, teddy bear, chocolate!"
    elif "bored" in command or "sad" in command:
        return "Cheer up! Grab a chocolate or chips!"
    return "Sorry, I didn't catch that. Try saying hello, suggest, or ask about sales."

# === Voice Thread ===
def voice_loop():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    command = recognizer.recognize_google(audio)
                    response = simple_response(command)
                    engine.say(response)
                    engine.runAndWait()
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print(f"Speech Recognition Error: {e}")
    except Exception as e:
        print(f"Voice assistant error: {e}")

threading.Thread(target=voice_loop, daemon=True).start()

# === USB Webcam Setup ===
cap = cv2.VideoCapture(0)  # USB webcam
time.sleep(2)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# === Load Sounds ===
try:
    beep = pygame.mixer.Sound("beep.wav")
    checkout_sound = pygame.mixer.Sound("success.wav")
except:
    beep = checkout_sound = None

# === Main Loop ===
while True:
    pygame.event.pump()
    screen.fill((30, 30, 30))

    try:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[Frame Error] Unable to read from webcam")
            continue

        result = model(frame)
        detected_labels = [x for x in result.names.values() if x in item_prices]

        for label in detected_labels:
            detection_memory[label] = detection_memory.get(label, 0) + 1
            disappear_memory[label] = 0
            if detection_memory[label] >= 5:
                cart[label] = cart.get(label, 0) + 1
                detection_memory[label] = 0

        for label in list(cart):
            if label not in detected_labels:
                disappear_memory[label] = disappear_memory.get(label, 0) + 1
                if disappear_memory[label] >= 3:
                    del cart[label]
                    if beep: beep.play()
                    engine.say(f"Alert: {label} removed!")
                    engine.runAndWait()

        # Draw UI
        y = 60
        total = 0
        for label, count in cart.items():
            icon = product_icons.get(label)
            if icon:
                screen.blit(pygame.transform.scale(icon, (60, 60)), (20, y))
            text = font.render(f"{label} x{count} - ${item_prices[label]*count:.2f}", True, (255, 255, 255))
            screen.blit(text, (100, y+10))
            y += 80
            total += item_prices[label] * count

        # Animate total
        if animated_total < total:
            animated_total += min(5, total - animated_total)
        elif animated_total > total:
            animated_total -= min(5, animated_total - total)
        screen.blit(font.render(f"Total: ${animated_total:.2f}", True, (0, 255, 0)), (500, 20))

        # Greeting and Tip
        screen.blit(font.render(greeting, True, (255, 255, 0)), (20, 10))
        screen.blit(font.render(random.choice(fun_tips), True, (200, 200, 255)), (20, 520))

        # Checkout Display
        if checkout_triggered and not checkout_message_displayed:
            items_str = ', '.join([f"{k} x{v}" for k, v in cart.items()])
            engine.say(f"You bought: {items_str}. Total amount is {total:.2f} dollars. Thank you for shopping!")
            engine.runAndWait()
            if checkout_sound: checkout_sound.play()
            screen.fill((0, 100, 0))
            screen.blit(font.render("Checkout Complete!", True, (255, 255, 255)), (250, 250))
            screen.blit(font.render("Thank you!", True, (255, 255, 0)), (310, 300))
            pygame.display.flip()
            time.sleep(4)
            checkout_message_displayed = True
            cart.clear()
            checkout_triggered = False

        pygame.display.update()
        clock.tick(60)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except Exception as e:
        print(f"Frame error: {e}")
        continue

cap.release()
pygame.quit()
