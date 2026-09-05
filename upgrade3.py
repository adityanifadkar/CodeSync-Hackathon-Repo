# ============================================================
# AI E-WASTE REE ANALYZER
# FINAL VERSION
#
# Dataset:
# C:\Users\User\Downloads\archive.zip
#
# Expected logical structure somewhere inside ZIP:
#
# train/
#   keyboard/
#   pcb/
#   speaker/
#   mouse/
#   printer/
#   microwave/
#
# test/
#   keyboard/
#   pcb/
#   speaker/
#   mouse/
#   printer/
#   microwave/
#
# FEATURES:
#   1. Automatically extracts ZIP
#   2. Automatically finds train/test folders
#   3. Uses ACTUAL folders as classes
#   4. Trains YOLO classification model once
#   5. Saves best model
#   6. Subsequent runs only load model
#   7. Live webcam classification
#   8. REE potential display
# ============================================================


import os
import zipfile
import shutil
import json
import cv2
import numpy as np

from pathlib import Path
from ultralytics import YOLO


# ============================================================
# 1. PATH CONFIGURATION
# ============================================================

ZIP_PATH = r"C:\Users\User\Downloads\archive.zip"

# Where ZIP will be extracted
EXTRACT_PATH = r"C:\Users\User\Downloads\REE_DATASET"

# These are FOUND AUTOMATICALLY
TRAIN_PATH = None
TEST_PATH = None

# Saved trained model
MODEL_PATH = (
    r"C:\Users\User\Downloads\REE_DATASET"
    r"\ewaste_classifier.pt"
)

# Saved class list
CLASS_FILE = (
    r"C:\Users\User\Downloads\REE_DATASET"
    r"\classes.json"
)


# ============================================================
# 2. TRAINING SETTINGS
# ============================================================

# If model already exists, it will NOT retrain.
TRAIN_MODEL = True

EPOCHS = 10

IMAGE_SIZE = 224

BATCH_SIZE = 16

CONFIDENCE_THRESHOLD = 0.60

CAMERA_INDEX = 0


# ============================================================
# 3. REE KNOWLEDGE BASE
#
# IMPORTANT:
# These are screening scores, NOT measured percentages.
# Replace with validated experimental data later.
# ============================================================

REE_DATABASE = {

    "keyboard": {
        "category": "Computer Peripheral",
        "ree_score": 10,
        "elements": [],
        "component": "Controller PCB / electronic contacts"
    },

    "pcb": {
        "category": "Electronic Circuit Board",
        "ree_score": 50,
        "elements": [
            "Cerium (Ce)",
            "Lanthanum (La)"
        ],
        "component": "Mounted electronic components"
    },

    "speaker": {
        "category": "Audio Device",
        "ree_score": 70,
        "elements": [
            "Neodymium (Nd)",
            "Praseodymium (Pr)",
            "Dysprosium (Dy)"
        ],
        "component": "Permanent magnet / speaker driver"
    },

    "mouse": {
        "category": "Computer Peripheral",
        "ree_score": 10,
        "elements": [],
        "component": "Controller PCB"
    },

    "printer": {
        "category": "Office Electronics",
        "ree_score": 35,
        "elements": [
            "Possible rare-earth materials"
        ],
        "component": "Motors / magnets / electronics"
    },

    "microwave": {
        "category": "Home Appliance",
        "ree_score": 15,
        "elements": [],
        "component": "Motor / transformer / electronics"
    },

    "unknown": {
        "category": "Unknown",
        "ree_score": 0,
        "elements": [],
        "component": "Unknown"
    }
}


# ============================================================
# 4. CREATE PROJECT DIRECTORY
# ============================================================

os.makedirs(
    EXTRACT_PATH,
    exist_ok=True
)


# ============================================================
# 5. EXTRACT ZIP
# ============================================================

def extract_dataset():

    print()
    print("=" * 65)
    print("DATASET EXTRACTION")
    print("=" * 65)

    print("ZIP FILE:")
    print(ZIP_PATH)

    if not os.path.isfile(ZIP_PATH):

        print()
        print("[ERROR] ZIP file not found.")

        return False


    # --------------------------------------------------------
    # Do not extract again if already present
    # --------------------------------------------------------

    if os.path.exists(
        EXTRACT_PATH
    ):

        print()
        print(
            "[INFO] Extraction folder already exists."
        )

        print(
            EXTRACT_PATH
        )

        return True


    print()
    print(
        "[INFO] Extracting archive..."
    )


    try:

        with zipfile.ZipFile(
            ZIP_PATH,
            "r"
        ) as zip_ref:

            zip_ref.extractall(
                EXTRACT_PATH
            )


        print(
            "[SUCCESS] ZIP extracted."
        )

        return True


    except Exception as error:

        print(
            "[ERROR] Extraction failed:"
        )

        print(
            error
        )

        return False


# ============================================================
# 6. FIND TRAIN AND TEST AUTOMATICALLY
# ============================================================

def find_dataset_folders():

    global TRAIN_PATH
    global TEST_PATH

    print()
    print("=" * 65)
    print("SEARCHING DATASET FOLDERS")
    print("=" * 65)


    train_candidates = []
    test_candidates = []


    # --------------------------------------------------------
    # Search recursively
    # --------------------------------------------------------

    for root, dirs, files in os.walk(
        EXTRACT_PATH
    ):

        root_path = Path(root)

        folder_name = root_path.name.lower()


        if folder_name == "train":

            train_candidates.append(
                root_path
            )


        if folder_name in [
            "test",
            "testing",
            "val",
            "validation"
        ]:

            test_candidates.append(
                root_path
            )


    # --------------------------------------------------------
    # Find best train folder
    # --------------------------------------------------------

    if train_candidates:

        # Prefer train folder that contains
        # multiple class directories.

        best_train = None
        best_class_count = 0


        for candidate in train_candidates:

            class_count = 0

            try:

                for child in candidate.iterdir():

                    if child.is_dir():

                        class_count += 1

            except Exception:

                continue


            if class_count > best_class_count:

                best_class_count = class_count

                best_train = candidate


        TRAIN_PATH = best_train


    # --------------------------------------------------------
    # Find test folder
    # --------------------------------------------------------

    if test_candidates:

        TEST_PATH = test_candidates[0]


    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print()
    print("TRAIN PATH:")
    print(TRAIN_PATH)

    print()
    print("TEST PATH:")
    print(TEST_PATH)


    if TRAIN_PATH is None:

        print()
        print("[ERROR] TRAIN folder was not found.")

        print()
        print("Python searched:")
        print(EXTRACT_PATH)

        print()
        print("Folders found:")

        for root, dirs, files in os.walk(
            EXTRACT_PATH
        ):

            print(
                root
            )

        return False


    return True


# ============================================================
# 7. FIND ACTUAL CLASSES
# ============================================================

def find_classes():

    print()
    print("=" * 65)
    print("DETECTING ACTUAL DEVICE CLASSES")
    print("=" * 65)


    classes = []


    for folder in sorted(
        Path(TRAIN_PATH).iterdir()
    ):

        if not folder.is_dir():

            continue


        # Check for images

        image_found = False


        for file in folder.rglob("*"):

            if (
                file.is_file()
                and
                file.suffix.lower()
                in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".bmp",
                    ".webp"
                ]
            ):

                image_found = True

                break


        if image_found:

            classes.append(
                folder.name
            )


    print()
    print(
        f"FOUND {len(classes)} CLASSES:"
    )


    for i, class_name in enumerate(
        classes
    ):

        print(
            f"{i}: {class_name}"
        )


    if len(classes) < 2:

        print()
        print(
            "[ERROR] Need at least 2 classes."
        )

        return None


    return classes


# ============================================================
# 8. TRAIN YOLO CLASSIFICATION MODEL
# ============================================================

def train_classifier():

    print()
    print("=" * 65)
    print("MODEL TRAINING")
    print("=" * 65)

    print()
    print("Training directory:")
    print(TRAIN_PATH)

    print()
    print("This happens ONLY when no trained model exists.")


    try:

        # Pretrained lightweight classification model
        model = YOLO(
            "yolo11n-cls.pt"
        )


        print()
        print("Starting training...")
        print(
            f"Epochs: {EPOCHS}"
        )


        model.train(

            data=str(
                Path(TRAIN_PATH).parent
            ),

            epochs=EPOCHS,

            imgsz=IMAGE_SIZE,

            batch=BATCH_SIZE,

            patience=3,

            pretrained=True,

            project=EXTRACT_PATH,

            name="ewaste_training",

            exist_ok=True,

            verbose=True

        )


        # ----------------------------------------------------
        # Locate best model
        # ----------------------------------------------------

        best_model = (
            Path(EXTRACT_PATH)
            /
            "ewaste_training"
            /
            "weights"
            /
            "best.pt"
        )


        if not best_model.exists():

            print()
            print(
                "[ERROR] best.pt was not created."
            )

            return None


        # ----------------------------------------------------
        # Copy best model
        # ----------------------------------------------------

        shutil.copy2(
            best_model,
            MODEL_PATH
        )


        print()
        print("=" * 65)
        print("TRAINING COMPLETE")
        print("=" * 65)

        print()
        print(
            "MODEL SAVED:"
        )

        print(
            MODEL_PATH
        )


        return YOLO(
            MODEL_PATH
        )


    except Exception as error:

        print()
        print(
            "[TRAINING ERROR]"
        )

        print(
            error
        )

        return None


# ============================================================
# 9. LOAD EXISTING MODEL
# ============================================================

def load_existing_model():

    print()
    print("=" * 65)
    print("LOADING EXISTING MODEL")
    print("=" * 65)

    print()
    print(
        MODEL_PATH
    )


    try:

        model = YOLO(
            MODEL_PATH
        )

        print()
        print(
            "[SUCCESS] Model loaded."
        )

        return model


    except Exception as error:

        print()
        print(
            "[ERROR] Model loading failed."
        )

        print(
            error
        )

        return None


# ============================================================
# 10. SAVE CLASS LIST
# ============================================================

def save_class_list(
    model
):

    names = model.names


    if isinstance(
        names,
        dict
    ):

        classes = [
            names[i]
            for i in range(
                len(names)
            )
        ]

    else:

        classes = list(
            names
        )


    with open(
        CLASS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            classes,
            file,
            indent=4
        )


    return classes


# ============================================================
# 11. GET REE INFORMATION
# ============================================================

def get_ree_data(
    device
):

    device = (
        device
        .lower()
        .strip()
    )


    # Direct match

    if device in REE_DATABASE:

        return REE_DATABASE[
            device
        ]


    # Partial match

    for key in REE_DATABASE:

        if key in device:

            return REE_DATABASE[
                key
            ]


    return REE_DATABASE[
        "unknown"
    ]


# ============================================================
# 12. CALCULATE REE SCREENING SCORE
# ============================================================

def calculate_ree_score(
    device,
    confidence
):

    database = get_ree_data(
        device
    )


    base_score = float(
        database.get(
            "ree_score",
            0
        )
    )


    # Model confidence contributes only partially.
    # This is NOT elemental concentration.

    score = (

        0.75 *
        base_score

        +

        0.25 *
        (
            confidence * 100
        )

    )


    score = max(
        0,
        min(
            score,
            100
        )
    )


    return score, database


# ============================================================
# 13. DRAW PANEL
# ============================================================

def draw_panel(
    frame,
    device,
    confidence,
    ree_score,
    database,
    hall="N/A",
    uv="N/A"
):

    h, w = frame.shape[:2]


    panel_width = 390

    panel_x = (
        w -
        panel_width
    )


    # --------------------------------------------------------
    # Background
    # --------------------------------------------------------

    cv2.rectangle(

        frame,

        (
            panel_x,
            0
        ),

        (
            w,
            h
        ),

        (
            20,
            20,
            20
        ),

        -1
    )


    x = (
        panel_x +
        18
    )

    y = 35


    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "AI E-WASTE REE ANALYZER",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.58,

        (
            0,
            255,
            255
        ),

        2
    )


    y += 38


    # --------------------------------------------------------
    # DEVICE
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "IDENTIFIED DEVICE",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.38,

        (
            160,
            160,
            160
        ),

        1
    )


    y += 28


    cv2.putText(

        frame,

        device.upper()[:30],

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.72,

        (
            255,
            255,
            255
        ),

        2
    )


    y += 35


    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    cv2.putText(

        frame,

        f"AI CONFIDENCE: "
        f"{confidence * 100:.2f}%",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.50,

        (
            0,
            255,
            150
        ),

        2
    )


    y += 35


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "CATEGORY",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.38,

        (
            160,
            160,
            160
        ),

        1
    )


    y += 24


    cv2.putText(

        frame,

        database.get(
            "category",
            "Unknown"
        )[:32],

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.46,

        (
            255,
            255,
            255
        ),

        1
    )


    y += 40


    # --------------------------------------------------------
    # REE SCORE
    # --------------------------------------------------------

    cv2.putText(

        frame,

        f"REE POTENTIAL: "
        f"{ree_score:.1f}%",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.58,

        (
            0,
            255,
            100
        ),

        2
    )


    y += 30


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if ree_score >= 70:

        status = "HIGH REE POTENTIAL"

        status_color = (
            0,
            255,
            100
        )

    elif ree_score >= 40:

        status = "MEDIUM REE POTENTIAL"

        status_color = (
            0,
            200,
            255
        )

    else:

        status = "LOW REE POTENTIAL"

        status_color = (
            100,
            150,
            255
        )


    cv2.putText(

        frame,

        status,

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        status_color,

        2
    )


    y += 38


    # --------------------------------------------------------
    # SENSOR VALUES
    # --------------------------------------------------------

    cv2.putText(

        frame,

        f"Hall Sensor: {hall}",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.42,

        (
            220,
            220,
            220
        ),

        1
    )


    y += 24


    cv2.putText(

        frame,

        f"UV Sensor: {uv}",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.42,

        (
            220,
            220,
            220
        ),

        1
    )


    y += 38


    # --------------------------------------------------------
    # IMPORTANT COMPONENT
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "REE-RELEVANT COMPONENT",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.37,

        (
            160,
            160,
            160
        ),

        1
    )


    y += 23


    cv2.putText(

        frame,

        database.get(
            "component",
            "Unknown"
        )[:35],

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.40,

        (
            255,
            255,
            255
        ),

        1
    )


    y += 40


    # --------------------------------------------------------
    # REE ELEMENTS
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "POSSIBLE REEs",

        (
            x,
            y
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.40,

        (
            0,
            230,
            255
        ),

        1
    )


    y += 25


    elements = database.get(
        "elements",
        []
    )


    if elements:

        for element in elements[:4]:

            cv2.putText(

                frame,

                str(element),

                (
                    x,
                    y
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.38,

                (
                    255,
                    255,
                    255
                ),

                1
            )

            y += 23

    else:

        cv2.putText(

            frame,

            "No known REE in database",

            (
                x,
                y
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.38,

            (
                170,
                170,
                170
            ),

            1
        )


    # --------------------------------------------------------
    # DISCLAIMER
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "REE score = screening potential",

        (
            x,
            h - 45
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.34,

        (
            150,
            150,
            150
        ),

        1
    )


    cv2.putText(

        frame,

        "Not direct elemental concentration",

        (
            x,
            h - 25
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.34,

        (
            150,
            150,
            150
        ),

        1
    )


# ============================================================
# 14. WEBCAM DETECTION
# ============================================================

def run_webcam(
    model,
    classes
):

    print()
    print("=" * 65)
    print("WEBCAM DETECTION")
    print("=" * 65)

    print()
    print("SPACE = Analyse object")
    print("Q     = Quit")


    camera = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW
    )


    if not camera.isOpened():

        # Retry without CAP_DSHOW

        camera = cv2.VideoCapture(
            CAMERA_INDEX
        )


    if not camera.isOpened():

        print(
            "[ERROR] Could not open webcam."
        )

        return


    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        1280
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        720
    )


    detected_device = "WAITING"

    confidence = 0.0

    ree_score = 0.0

    database = get_ree_data(
        "unknown"
    )


    while True:

        ret, frame = camera.read()


        if not ret:

            print(
                "[ERROR] Camera frame failed."
            )

            break


        # Mirror

        frame = cv2.flip(
            frame,
            1
        )


        h, w = frame.shape[:2]


        # ----------------------------------------------------
        # TARGET BOX
        # ----------------------------------------------------

        box_size = 220

        cx = int(
            w * 0.32
        )

        cy = int(
            h * 0.50
        )


        x1 = max(
            0,
            cx - box_size
        )

        y1 = max(
            0,
            cy - box_size
        )


        x2 = min(
            w,
            cx + box_size
        )

        y2 = min(
            h,
            cy + box_size
        )


        cv2.rectangle(

            frame,

            (
                x1,
                y1
            ),

            (
                x2,
                y2
            ),

            (
                0,
                255,
                255
            ),

            2
        )


        cv2.putText(

            frame,

            "PLACE DEVICE HERE",

            (
                x1,
                y1 - 10
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.52,

            (
                0,
                255,
                255
            ),

            2
        )


        # ----------------------------------------------------
        # PANEL
        # ----------------------------------------------------

        draw_panel(

            frame,

            detected_device,

            confidence,

            ree_score,

            database

        )


        # ----------------------------------------------------
        # SHOW
        # ----------------------------------------------------

        cv2.imshow(

            "AI E-WASTE REE ANALYZER",

            frame

        )


        key = (
            cv2.waitKey(1)
            &
            0xFF
        )


        # ----------------------------------------------------
        # QUIT
        # ----------------------------------------------------

        if key == ord(
            "q"
        ):

            break


        if key == 27:

            break


        # ----------------------------------------------------
        # ANALYSE
        # ----------------------------------------------------

        if key == 32:

            roi = frame[
                y1:y2,
                x1:x2
            ]


            if roi.size == 0:

                continue


            print()
            print("=" * 60)
            print("ANALYSING OBJECT")
            print("=" * 60)


            # ------------------------------------------------
            # MODEL PREDICTION
            # ------------------------------------------------

            try:

                results = model.predict(

                    roi,

                    imgsz=IMAGE_SIZE,

                    verbose=False

                )

            except Exception as error:

                print(
                    "[PREDICTION ERROR]",
                    error
                )

                continue


            if not results:

                print(
                    "No result."
                )

                continue


            result = results[0]


            if result.probs is None:

                print(
                    "Classification probabilities unavailable."
                )

                continue


            probs = result.probs


            # ------------------------------------------------
            # BEST CLASS
            # ------------------------------------------------

            best_index = int(
                probs.top1
            )


            confidence = float(
                probs.top1conf
            )


            predicted_class = (
                classes[
                    best_index
                ]
            )


            # ------------------------------------------------
            # LOW CONFIDENCE
            # ------------------------------------------------

            if confidence < CONFIDENCE_THRESHOLD:

                detected_device = (
                    "UNKNOWN"
                )

                database = get_ree_data(
                    "unknown"
                )

                ree_score = 0

                print()
                print(
                    "LOW CONFIDENCE"
                )

                print(
                    f"Confidence: "
                    f"{confidence * 100:.2f}%"
                )


            else:

                detected_device = (
                    predicted_class
                )


                # --------------------------------------------
                # REE
                # --------------------------------------------

                ree_score, database = (
                    calculate_ree_score(

                        predicted_class,

                        confidence

                    )
                )


                print()
                print(
                    "DEVICE:",
                    predicted_class
                )

                print(
                    f"AI CONFIDENCE: "
                    f"{confidence * 100:.2f}%"
                )

                print(
                    f"REE POTENTIAL: "
                    f"{ree_score:.2f}%"
                )

                print(
                    "CATEGORY:",
                    database.get(
                        "category"
                    )
                )

                print(
                    "IMPORTANT COMPONENT:",
                    database.get(
                        "component"
                    )
                )

                print(
                    "REEs:",
                    database.get(
                        "elements"
                    )
                )


            # ------------------------------------------------
            # TOP 3
            # ------------------------------------------------

            print()
            print(
                "TOP PREDICTIONS:"
            )


            try:

                top5 = probs.top5

                top5conf = (
                    probs.top5conf
                )


                for i in range(
                    min(
                        3,
                        len(top5)
                    )
                ):

                    idx = int(
                        top5[i]
                    )

                    conf = float(
                        top5conf[i]
                    )


                    print(

                        f"{i + 1}. "
                        f"{classes[idx]} "
                        f"= "
                        f"{conf * 100:.2f}%"

                    )

            except Exception:

                pass


            print(
                "=" * 60
            )


    camera.release()

    cv2.destroyAllWindows()


# ============================================================
# 15. MAIN
# ============================================================

def main():

    print()
    print(
        "############################################################"
    )

    print(
        "              AI E-WASTE REE ANALYZER"
    )

    print(
        "############################################################"
    )


    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    if not extract_dataset():

        return


    # --------------------------------------------------------
    # FIND DATASET
    # --------------------------------------------------------

    if not find_dataset_folders():

        return


    # --------------------------------------------------------
    # SHOW ACTUAL CLASSES
    # --------------------------------------------------------

    actual_classes = find_classes()


    if actual_classes is None:

        return


    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    if os.path.exists(
        MODEL_PATH
    ):

        print()
        print(
            "Existing trained model detected."
        )

        print(
            "Skipping training."
        )

        model = load_existing_model()


    else:

        print()
        print(
            "No trained model found."
        )

        print(
            "Training model for first run..."
        )

        model = train_classifier()


    if model is None:

        return


    # --------------------------------------------------------
    # CLASSES FROM MODEL
    # --------------------------------------------------------

    classes = save_class_list(
        model
    )


    print()
    print("=" * 65)
    print("FINAL MODEL CLASSES")
    print("=" * 65)


    for i, name in enumerate(
        classes
    ):

        print(
            f"{i}: {name}"
        )


    # --------------------------------------------------------
    # WEBCAM
    # --------------------------------------------------------

    run_webcam(

        model,

        classes

    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()