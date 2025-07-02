import os

dataset_dir = "D:/YugMorph/dataset/all_images"

# Check if directory exists
if not os.path.exists(dataset_dir):
    print(f"❌ Error: Directory '{dataset_dir}' does not exist!")
else:
    print(f"✅ Directory '{dataset_dir}' found.")

# List images
image_files = [f for f in os.listdir(dataset_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]

# Print result
if not image_files:
    print("❌ No images found in 'all_images' folder!")
else:
    print(f"✅ Found {len(image_files)} images.")
    print("📂 Sample images:", image_files[:5])  # Show first 5 images
