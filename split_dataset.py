import os
import shutil
import random


dataset_dir = "D:/YugMorph/dataset"
images_dir = os.path.join(dataset_dir, "all_images")
labels_dir = os.path.join(dataset_dir, "labels")
output_dir = "D:/YugMorph/yolov5/dataset"

for split in ['train', 'val', 'test']:
    os.makedirs(os.path.join(output_dir, 'images', split), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'labels', split), exist_ok=True)


image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
print(f"📸 Found {len(image_files)} images.")  

random.shuffle(image_files)

train_split = int(0.7 * len(image_files))
val_split = int(0.85 * len(image_files))

train_files = image_files[:train_split]
val_files = image_files[train_split:val_split]
test_files = image_files[val_split:]

def move_files(file_list, split):
    copied_images = 0
    copied_labels = 0

    for file in file_list:
        src_img = os.path.join(images_dir, file)
        dst_img = os.path.join(output_dir, 'images', split, file)

        if os.path.exists(src_img): 
            shutil.copy(src_img, dst_img)
            copied_images += 1
        else:
            print(f" Image not found: {src_img}")

        label_file = file.replace('.jpg', '.txt').replace('.png', '.txt')
        src_label = os.path.join(labels_dir, label_file)
        dst_label = os.path.join(output_dir, 'labels', split, label_file)

        if os.path.exists(src_label):
            shutil.copy(src_label, dst_label)
            copied_labels += 1
        else:
            print(f" Label not found for {file}")

    print(f" {copied_images} images and {copied_labels} labels copied to '{split}' set.")


move_files(train_files, 'train')
move_files(val_files, 'val')
move_files(test_files, 'test')

print("Dataset successfully split!")
