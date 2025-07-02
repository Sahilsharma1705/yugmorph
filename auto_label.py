import os

labels_path = "D:/YugMorph/dataset/labels/train"  # Change this if needed
num_classes = 4  # Ensure this matches 'nc' in data.yaml

# Iterate over label files
for file in os.listdir(labels_path):
    if file.endswith(".txt"):
        file_path = os.path.join(labels_path, file)

        with open(file_path, "r") as f:
            lines = f.readlines()

        # Check if any invalid label exists 
        if any(int(line.split()[0]) >= num_classes for line in lines):
            print(f"🗑️ Deleting {file}: Contains invalid class labels")
            os.remove(file_path)  # Delete the file

print("✅ All incorrect label files have been deleted successfully!")
