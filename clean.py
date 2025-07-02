import os
import yaml

# === CONFIGURATION ===
labels_dir = 'D:/YugMorph/dataset/labels'  # Path to labels
data_yaml_path = 'D:/YugMorph/dataset/data.yaml'  # Path to data.yaml

# Original full class list (from your dataset's original data.yaml)
original_class_list = [
    'chips', 'cold drink', 'laptop', 'teddy bear', 'book', 'pen',
    'bottle', 'watch', 'phone', 'clock', 'chocolates'
]

# Only keep these classes
keep_classes = ['teddy bear', 'chips', 'laptop', 'pen', 'cold drink', 'book']

# === BUILD MAPPING: old_class_id -> new_class_id ===
class_id_map = {i: keep_classes.index(cls) for i, cls in enumerate(original_class_list) if cls in keep_classes}
valid_ids = set(class_id_map.keys())

print(f"\n🔎 Keeping classes: {keep_classes}")
print(f"🗺️  Class ID Mapping: {class_id_map}\n")

# === PROCESS LABEL FILES ===
for split in ['train', 'val']:
    folder = os.path.join(labels_dir, split)
    if not os.path.exists(folder):
        print(f"⚠️ Folder {folder} doesn't exist, skipping...")
        continue

    for file in os.listdir(folder):
        if not file.endswith('.txt'):
            continue

        file_path = os.path.join(folder, file)
        with open(file_path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            class_id = int(parts[0])
            if class_id in valid_ids:
                new_id = class_id_map[class_id]
                new_line = ' '.join([str(new_id)] + parts[1:]) + '\n'
                new_lines.append(new_line)

        # Overwrite file with cleaned labels
        with open(file_path, 'w') as f:
            f.writelines(new_lines)

        print(f"✅ Cleaned {file_path} - {len(new_lines)} valid labels kept.")

# === UPDATE data.yaml ===
if os.path.exists(data_yaml_path):
    with open(data_yaml_path, 'r') as f:
        data_yaml = yaml.safe_load(f)

    data_yaml['nc'] = len(keep_classes)
    data_yaml['names'] = keep_classes

    with open(data_yaml_path, 'w') as f:
        yaml.dump(data_yaml, f)

    print(f"\n✅ Updated data.yaml with {len(keep_classes)} classes.")
else:
    print(f"\n❌ data.yaml not found at {data_yaml_path}")
