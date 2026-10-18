"""Prompt 17 — offline fallback classifier (STRETCH GOAL, not run in this build).

Per the implementation guide's own cut list: training and validating a real
on-device model is multi-day work with zero visible difference in a live demo
on good wifi. This script is written and ready, but intentionally NOT executed
here — running it requires downloading the full PlantVillage image set, which
is a multi-GB dataset and a genuinely multi-hour training job, not something
to run inline in a build session. Treat this as the "designed for" artifact
for the architecture slide, not a working deliverable yet.

To actually run it:
    pip install tensorflow pillow
    python train_offline_fallback.py --data-dir /path/to/plantvillage/tomato
"""
import argparse
import os

TARGET_CLASSES = [
    "early_blight", "late_blight", "leaf_curl_virus", "bacterial_wilt",
    "fusarium_wilt", "blossom_end_rot", "septoria_leaf_spot",
    "spider_mite_damage", "healthy",
]


def build_and_train(data_dir: str, output_path: str, epochs: int = 10):
    import tensorflow as tf

    img_size = (160, 160)  # small input size keeps the exported model under ~10MB
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="training", seed=42,
        image_size=img_size, batch_size=32,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="validation", seed=42,
        image_size=img_size, batch_size=32,
    )

    base_model = tf.keras.applications.MobileNetV3Small(
        input_shape=img_size + (3,), include_top=False, weights="imagenet",
    )
    base_model.trainable = False  # transfer learning keeps training fast and the model small

    model = tf.keras.Sequential([
        base_model,
        tf.keras.layers.GlobalAveragePooling2D(),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(len(TARGET_CLASSES), activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(train_ds, validation_data=val_ds, epochs=epochs)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]  # quantization keeps the .tflite small
    tflite_model = converter.convert()

    with open(output_path, "wb") as f:
        f.write(tflite_model)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Wrote {output_path} ({size_mb:.1f} MB)")
    if size_mb > 10:
        print("WARNING: over the 10MB target for a low-end Android device — "
              "increase quantization or shrink img_size further.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, help="Folder of class-named subfolders of tomato leaf images")
    parser.add_argument("--output", default="../backend/offline_model.tflite")
    parser.add_argument("--epochs", type=int, default=10)
    args = parser.parse_args()
    build_and_train(args.data_dir, args.output, args.epochs)
