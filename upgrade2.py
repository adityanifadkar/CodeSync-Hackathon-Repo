import cv2
import requests
import json
import time
import re
import os
import threading

from ultralytics import YOLOWorld


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_NAME = "AI E-WASTE REE ANALYZER"

# ------------------------------------------------------------
# ESP32
# ------------------------------------------------------------

ESP32_IP = "192.168.1.100"
ESP32_URL = f"http://{ESP32_IP}/sensor"

SENSOR_INTERVAL = 1.0


# ------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------

DATABASE_FILE = "ree_knowledge_database.json"


# ------------------------------------------------------------
# CAMERA
# ------------------------------------------------------------

CAMERA_INDEX = 0

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

CAMERA_FPS = 30


# ------------------------------------------------------------
# YOLO-WORLD
# ------------------------------------------------------------

MODEL_NAME = "yolov8s-worldv2.pt"

YOLO_IMAGE_SIZE = 416

YOLO_CONFIDENCE = 0.30

# Run AI every N frames.
# 2 = faster response
# 3 = lower CPU usage
DETECTION_INTERVAL = 2


# ------------------------------------------------------------
# STABILITY
# ------------------------------------------------------------

# Object must be detected repeatedly before we search internet.
STABLE_FRAMES_REQUIRED = 5


# ------------------------------------------------------------
# INTERNET
# ------------------------------------------------------------

WEB_SEARCH_COOLDOWN = 20


# ============================================================
# E-WASTE VOCABULARY
# ============================================================

EWASTE_CLASSES = [

    "hard disk drive",
    "HDD",
    "solid state drive",
    "SSD",

    "computer speaker",
    "speaker",

    "earphones",
    "earbuds",
    "wireless earbuds",
    "headphones",

    "smartphone",
    "mobile phone",
    "cell phone",

    "laptop",
    "desktop computer",

    "motherboard",
    "printed circuit board",
    "PCB",
    "circuit board",

    "RAM module",
    "computer memory",

    "graphics card",
    "GPU",

    "CPU",
    "computer processor",

    "computer mouse",
    "computer keyboard",

    "USB flash drive",
    "USB drive",

    "power supply",
    "SMPS",

    "electric motor",
    "DC motor",

    "transformer",

    "computer fan",
    "cooling fan",

    "router",
    "WiFi router",

    "remote control",

    "printer",

    "camera",

    "television",

    "monitor",

    "battery",

    "electronic circuit",

    "electronic component"
]


# ============================================================
# ALIASES
# ============================================================

ALIASES = {

    "hard disk drive": "hard disk",
    "hdd": "hard disk",
    "hard drive": "hard disk",

    "solid state drive": "ssd",
    "ssd": "ssd",

    "computer speaker": "speaker",

    "earbud": "earbuds",
    "wireless earbuds": "earbuds",
    "bluetooth earbuds": "earbuds",

    "earphone": "earphones",

    "headphone": "headphones",

    "smartphone": "mobile phone",
    "cell phone": "mobile phone",

    "notebook": "laptop",

    "desktop computer": "computer",

    "printed circuit board": "pcb",
    "circuit board": "pcb",
    "motherboard": "motherboard",

    "ram module": "ram",

    "computer memory": "ram",

    "graphics card": "graphics card",
    "gpu": "graphics card",

    "computer processor": "cpu",

    "usb flash drive": "usb drive",
    "usb drive": "usb drive",

    "power supply": "power supply",
    "smps": "power supply",

    "electric motor": "electric motor",
    "dc motor": "electric motor",

    "cooling fan": "fan",
    "computer fan": "fan",

    "wifi router": "router"
}


# ============================================================
# REE KNOWLEDGE DATABASE
# ============================================================

DEFAULT_DATABASE = {

    "hard disk": {

        "category": "Storage device",

        "ree": {
            "Neodymium (Nd)": "High",
            "Praseodymium (Pr)": "Possible",
            "Dysprosium (Dy)": "Possible"
        },

        "ree_score": 85,

        "important_component":
            "Permanent magnet in HDD actuator/spindle system",

        "details":
            "Hard disk drives commonly contain rare-earth permanent magnets, especially neodymium-based magnets.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "speaker": {

        "category": "Audio device",

        "ree": {
            "Neodymium (Nd)": "Possible",
            "Praseodymium (Pr)": "Possible",
            "Dysprosium (Dy)": "Possible"
        },

        "ree_score": 70,

        "important_component":
            "Permanent magnet",

        "details":
            "Some speakers use rare-earth permanent magnets such as neodymium magnets.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "earbuds": {

        "category": "Audio device",

        "ree": {
            "Neodymium (Nd)": "Possible",
            "Praseodymium (Pr)": "Possible"
        },

        "ree_score": 55,

        "important_component":
            "Miniature speaker driver",

        "details":
            "Small audio drivers can contain permanent magnets, including rare-earth magnet materials.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "earphones": {

        "category": "Audio device",

        "ree": {
            "Neodymium (Nd)": "Possible"
        },

        "ree_score": 50,

        "important_component":
            "Speaker driver",

        "details":
            "Some earphone drivers use permanent magnets.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "headphones": {

        "category": "Audio device",

        "ree": {
            "Neodymium (Nd)": "Possible"
        },

        "ree_score": 55,

        "important_component":
            "Speaker driver",

        "details":
            "Some headphone drivers use permanent magnets.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "mobile phone": {

        "category": "Mobile electronics",

        "ree": {
            "Neodymium (Nd)": "Possible",
            "Praseodymium (Pr)": "Possible",
            "Dysprosium (Dy)": "Possible"
        },

        "ree_score": 50,

        "important_component":
            "Speakers, vibration motor and electronic components",

        "details":
            "Mobile devices contain many components and may contain rare-earth materials in magnets and other components.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "laptop": {

        "category": "Computer",

        "ree": {
            "Neodymium (Nd)": "Possible",
            "Praseodymium (Pr)": "Possible"
        },

        "ree_score": 50,

        "important_component":
            "Speakers, motors and electronic components",

        "details":
            "Laptops contain multiple components that may contain rare-earth materials.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "motherboard": {

        "category": "Electronic circuit board",

        "ree": {
            "Cerium (Ce)": "Possible",
            "Lanthanum (La)": "Possible"
        },

        "ree_score": 40,

        "important_component":
            "Electronic components",

        "details":
            "Circuit boards contain many materials and components. Exact REE content varies significantly.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "pcb": {

        "category": "Electronic circuit board",

        "ree": {
            "Cerium (Ce)": "Possible",
            "Lanthanum (La)": "Possible"
        },

        "ree_score": 35,

        "important_component":
            "Electronic components",

        "details":
            "REE content depends strongly on the specific components mounted on the board.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "ram": {

        "category": "Computer memory",

        "ree": {},

        "ree_score": 20,

        "important_component":
            "Memory ICs",

        "details":
            "REE potential is highly dependent on the exact device and materials.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "graphics card": {

        "category": "Computer component",

        "ree": {
            "Neodymium (Nd)": "Possible"
        },

        "ree_score": 40,

        "important_component":
            "Cooling fans and electronic components",

        "details":
            "Graphics cards contain motors, fans and many electronic components.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "cpu": {

        "category": "Computer component",

        "ree": {},

        "ree_score": 20,

        "important_component":
            "Semiconductor package",

        "details":
            "REE potential cannot be reliably estimated from visual identification alone.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "usb drive": {

        "category": "Storage device",

        "ree": {},

        "ree_score": 15,

        "important_component":
            "Flash memory and controller",

        "details":
            "REE potential varies by construction and component materials.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "electric motor": {

        "category": "Motor",

        "ree": {
            "Neodymium (Nd)": "Possible",
            "Praseodymium (Pr)": "Possible",
            "Dysprosium (Dy)": "Possible"
        },

        "ree_score": 75,

        "important_component":
            "Permanent magnet",

        "details":
            "Some permanent-magnet motors use rare-earth magnet materials.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "fan": {

        "category": "Motor/electronic component",

        "ree": {
            "Neodymium (Nd)": "Possible"
        },

        "ree_score": 40,

        "important_component":
            "Electric motor",

        "details":
            "REE potential depends on the type of motor used.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "power supply": {

        "category": "Power electronics",

        "ree": {},

        "ree_score": 20,

        "important_component":
            "Transformer and electronic components",

        "details":
            "REE content varies with the specific design and components.",

        "source":
            "Project knowledge base",

        "verified":
            False
    },


    "unknown": {

        "category": "Unknown",

        "ree": {},

        "ree_score": 10,

        "important_component":
            "Unknown",

        "details":
            "Object requires further identification.",

        "source":
            "Default",

        "verified":
            False
    }
}


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def save_database(database):

    try:

        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                database,
                file,
                indent=4,
                ensure_ascii=False
            )

    except Exception as e:

        print("Database save error:", e)


def load_database():

    if os.path.exists(DATABASE_FILE):

        try:

            with open(
                DATABASE_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except Exception as e:

            print("Database error:", e)

    save_database(DEFAULT_DATABASE)

    return DEFAULT_DATABASE.copy()


REE_DATABASE = load_database()


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value, minimum, maximum):

    if value is None:
        return 0

    if maximum <= minimum:
        return 0

    value = max(
        minimum,
        min(value, maximum)
    )

    return (
        (value - minimum)
        /
        (maximum - minimum)
    ) * 100


# ============================================================
# FIND DATABASE COMPONENT
# ============================================================

def find_component(name):

    if not name:
        return "unknown"

    name = name.lower().strip()

    if name in REE_DATABASE:
        return name

    if name in ALIASES:

        return ALIASES[name]

    for alias, component in ALIASES.items():

        if alias in name:

            return component

    for component in REE_DATABASE:

        if component in name:

            return component

    return "unknown"


# ============================================================
# ESP32 DATA
# ============================================================

sensor_data = {

    "hall": None,

    "uv": None,

    "connected": False,

    "last_update": 0
}


def sensor_worker():

    while True:

        try:

            response = requests.get(
                ESP32_URL,
                timeout=0.4
            )

            if response.status_code == 200:

                data = response.json()

                sensor_data["hall"] = float(
                    data.get("hall", 0)
                )

                sensor_data["uv"] = float(
                    data.get("uv", 0)
                )

                sensor_data["connected"] = True

                sensor_data["last_update"] = time.time()

            else:

                sensor_data["connected"] = False

        except:

            sensor_data["connected"] = False

        time.sleep(SENSOR_INTERVAL)


# ============================================================
# INTERNET SEARCH
# ============================================================

web_data = {

    "title": "",

    "summary": "",

    "url": "",

    "status": "Not searched"
}


def internet_search(query):

    try:

        api_url = (
            "https://en.wikipedia.org/w/api.php"
        )

        params = {

            "action": "opensearch",

            "search": query,

            "limit": 3,

            "namespace": 0,

            "format": "json"
        }

        response = requests.get(
            api_url,
            params=params,
            timeout=4
        )

        if response.status_code != 200:

            return None

        result = response.json()

        titles = result[1]

        if not titles:

            return None

        title = titles[0]

        summary_url = (
            "https://en.wikipedia.org/"
            "api/rest_v1/page/summary/"
            +
            title.replace(" ", "_")
        )

        summary_response = requests.get(
            summary_url,
            timeout=4
        )

        if summary_response.status_code != 200:

            return None

        summary_data = summary_response.json()

        return {

            "title":
                summary_data.get(
                    "title",
                    title
                ),

            "summary":
                summary_data.get(
                    "extract",
                    ""
                ),

            "url":
                summary_data.get(
                    "content_urls",
                    {}
                ).get(
                    "desktop",
                    {}
                ).get(
                    "page",
                    ""
                )
        }

    except Exception as e:

        print("Internet search error:", e)

        return None


# ============================================================
# BACKGROUND WEB SEARCH
# ============================================================

web_lock = threading.Lock()

web_search_running = False

last_web_search_time = 0

last_web_object = ""


def web_search_worker(object_name):

    global web_search_running
    global last_web_search_time
    global last_web_object

    try:

        query = (
            object_name
            +
            " rare earth elements materials"
        )

        print()
        print("=" * 60)
        print("INTERNET LOOKUP")
        print("=" * 60)
        print("Query:", query)

        result = internet_search(query)

        with web_lock:

            if result:

                web_data["title"] = result["title"]

                web_data["summary"] = result["summary"]

                web_data["url"] = result["url"]

                web_data["status"] = "Internet information found"

                print("Found:", result["title"])

            else:

                web_data["status"] = "No web result"

        last_web_search_time = time.time()

        last_web_object = object_name

    finally:

        web_search_running = False


def start_web_search(object_name):

    global web_search_running

    if web_search_running:

        return

    if (
        time.time()
        -
        last_web_search_time
        <
        WEB_SEARCH_COOLDOWN
    ):

        return

    web_search_running = True

    thread = threading.Thread(
        target=web_search_worker,
        args=(object_name,),
        daemon=True
    )

    thread.start()


# ============================================================
# REE SCORE
# ============================================================

def calculate_ree_score(component):

    database = REE_DATABASE.get(
        component,
        REE_DATABASE["unknown"]
    )

    base_score = float(
        database.get(
            "ree_score",
            10
        )
    )

    hall = sensor_data["hall"]

    uv = sensor_data["uv"]

    # --------------------------------------------------------
    # If sensors are unavailable, use database score.
    # --------------------------------------------------------

    if hall is None or uv is None:

        return base_score


    hall_score = normalize(
        hall,
        0,
        4095
    )

    uv_score = normalize(
        uv,
        0,
        4095
    )


    # --------------------------------------------------------
    # SENSOR FUSION
    # --------------------------------------------------------

    final_score = (

        0.65 * base_score

        +

        0.25 * hall_score

        +

        0.10 * uv_score
    )


    return max(
        0,
        min(
            final_score,
            100
        )
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_score(score):

    if score >= 75:

        return "HIGH REE POTENTIAL"

    elif score >= 45:

        return "MEDIUM REE POTENTIAL"

    else:

        return "LOW REE POTENTIAL"


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(
    CAMERA_INDEX,
    cv2.CAP_DSHOW
)

camera.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    CAMERA_WIDTH
)

camera.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    CAMERA_HEIGHT
)

camera.set(
    cv2.CAP_PROP_FPS,
    CAMERA_FPS
)

camera.set(
    cv2.CAP_PROP_BUFFERSIZE,
    1
)


if not camera.isOpened():

    print("ERROR: Camera could not be opened.")

    raise SystemExit


# ============================================================
# YOLO-WORLD
# ============================================================

print()
print("Loading YOLO-World...")

model = YOLOWorld(
    MODEL_NAME
)

print("YOLO-World loaded.")

print("Setting e-waste vocabulary...")

model.set_classes(
    EWASTE_CLASSES
)

print("E-waste vocabulary loaded.")


# ============================================================
# DETECTION VARIABLES
# ============================================================

frame_count = 0

last_detections = []

detected_object = "Waiting..."

detected_confidence = 0

stable_object = ""

stable_count = 0

last_component = "unknown"


# ============================================================
# FPS
# ============================================================

fps = 0

fps_counter = 0

fps_start = time.time()


# ============================================================
# START SENSOR THREAD
# ============================================================

sensor_thread = threading.Thread(
    target=sensor_worker,
    daemon=True
)

sensor_thread.start()


# ============================================================
# WINDOW
# ============================================================

WINDOW_NAME = "AI E-WASTE REE ANALYZER"

cv2.namedWindow(
    WINDOW_NAME,
    cv2.WINDOW_NORMAL
)


# ============================================================
# MAIN LOOP
# ============================================================

print()
print("=" * 60)
print(PROJECT_NAME)
print("=" * 60)
print()
print("Press Q to quit.")
print()


while True:

    # --------------------------------------------------------
    # READ CAMERA
    # --------------------------------------------------------

    ret, frame = camera.read()

    if not ret:

        print("Camera frame error.")

        break


    frame_count += 1


    # --------------------------------------------------------
    # FPS
    # --------------------------------------------------------

    fps_counter += 1

    elapsed = (
        time.time()
        -
        fps_start
    )

    if elapsed >= 1:

        fps = (
            fps_counter
            /
            elapsed
        )

        fps_counter = 0

        fps_start = time.time()


    # --------------------------------------------------------
    # YOLO DETECTION
    # --------------------------------------------------------

    if (
        frame_count
        %
        DETECTION_INTERVAL
        ==
        0
    ):

        try:

            results = model.predict(

                frame,

                imgsz=YOLO_IMAGE_SIZE,

                conf=YOLO_CONFIDENCE,

                verbose=False,

                device="cpu"
            )

            detections = []

            best_name = "No e-waste"

            best_conf = 0


            for result in results:

                if result.boxes is None:

                    continue


                for box in result.boxes:

                    confidence = float(
                        box.conf[0]
                    )

                    class_id = int(
                        box.cls[0]
                    )

                    name = model.names[
                        class_id
                    ]


                    if confidence > best_conf:

                        best_conf = confidence

                        best_name = name


                    detections.append(

                        (
                            box,
                            name,
                            confidence
                        )

                    )


            last_detections = detections

            detected_object = best_name

            detected_confidence = best_conf


        except Exception as e:

            print(
                "YOLO error:",
                e
            )


    # --------------------------------------------------------
    # STABLE OBJECT DETECTION
    # --------------------------------------------------------

    if detected_object != "No e-waste":

        if detected_object == stable_object:

            stable_count += 1

        else:

            stable_object = detected_object

            stable_count = 1


    else:

        stable_object = ""

        stable_count = 0


    # --------------------------------------------------------
    # DATABASE IDENTIFICATION
    # --------------------------------------------------------

    if stable_count >= STABLE_FRAMES_REQUIRED:

        component = find_component(
            stable_object
        )

        last_component = component

        # ----------------------------------------------------
        # INTERNET SEARCH ONLY ONCE FOR NEW OBJECT
        # ----------------------------------------------------

        if component == "unknown":

            start_web_search(
                stable_object
            )


    # --------------------------------------------------------
    # REE SCORE
    # --------------------------------------------------------

    ree_score = calculate_ree_score(
        last_component
    )

    classification = classify_score(
        ree_score
    )


    # --------------------------------------------------------
    # DATABASE DATA
    # --------------------------------------------------------

    database_info = REE_DATABASE.get(

        last_component,

        REE_DATABASE["unknown"]

    )


    ree_elements = database_info.get(
        "ree",
        {}
    )


    category = database_info.get(
        "category",
        "Unknown"
    )


    important_component = database_info.get(
        "important_component",
        "Unknown"
    )


    # --------------------------------------------------------
    # DRAW DETECTIONS
    # --------------------------------------------------------

    for box, name, confidence in last_detections:

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )


        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            2
        )


        label = (
            f"{name} "
            f"{confidence * 100:.0f}%"
        )


        cv2.putText(

            frame,

            label,

            (
                x1,
                max(
                    20,
                    y1 - 8
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.55,

            (0, 255, 0),

            2
        )


    # ========================================================
    # INFORMATION PANEL
    # ========================================================

    panel_width = 330

    h, w = frame.shape[:2]

    panel_x = max(
        0,
        w - panel_width
    )


    # Dark panel

    cv2.rectangle(

        frame,

        (panel_x, 0),

        (w, h),

        (25, 25, 25),

        -1
    )


    x = panel_x + 12

    y = 25


    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "AI E-WASTE ANALYZER",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (255, 255, 255),

        2
    )


    y += 30


    # --------------------------------------------------------
    # FPS
    # --------------------------------------------------------

    cv2.putText(

        frame,

        f"FPS: {fps:.1f}",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.5,

        (0, 255, 255),

        1
    )


    y += 28


    # --------------------------------------------------------
    # OBJECT
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "DETECTED OBJECT",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.42,

        (170, 170, 170),

        1
    )


    y += 20


    cv2.putText(

        frame,

        detected_object[:25],

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.50,

        (255, 255, 255),

        2
    )


    y += 22


    cv2.putText(

        frame,

        f"Confidence: "
        f"{detected_confidence * 100:.1f}%",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.42,

        (220, 220, 220),

        1
    )


    y += 30


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "CATEGORY",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.42,

        (170, 170, 170),

        1
    )


    y += 19


    cv2.putText(

        frame,

        category[:30],

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (255, 255, 255),

        1
    )


    y += 28


    # --------------------------------------------------------
    # IMPORTANT COMPONENT
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "REE-BEARING COMPONENT",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.38,

        (170, 170, 170),

        1
    )


    y += 19


    cv2.putText(

        frame,

        important_component[:32],

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.40,

        (255, 255, 255),

        1
    )


    y += 28


    # --------------------------------------------------------
    # HALL
    # --------------------------------------------------------

    hall = sensor_data["hall"]

    if hall is None:

        hall_text = "Disconnected"

    else:

        hall_text = f"{hall:.0f}"


    cv2.putText(

        frame,

        f"Hall Sensor: {hall_text}",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (255, 255, 255),

        1
    )


    y += 25


    # --------------------------------------------------------
    # UV
    # --------------------------------------------------------

    uv = sensor_data["uv"]

    if uv is None:

        uv_text = "Disconnected"

    else:

        uv_text = f"{uv:.0f}"


    cv2.putText(

        frame,

        f"UV Sensor: {uv_text}",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (255, 255, 255),

        1
    )


    y += 30


    # --------------------------------------------------------
    # REE SCORE
    # --------------------------------------------------------

    cv2.putText(

        frame,

        f"REE POTENTIAL: {ree_score:.1f}%",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.53,

        (0, 255, 255),

        2
    )


    y += 25


    cv2.putText(

        frame,

        classification,

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.40,

        (0, 255, 0),

        2
    )


    y += 30


    # --------------------------------------------------------
    # REEs
    # --------------------------------------------------------

    cv2.putText(

        frame,

        "POSSIBLE REEs",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.40,

        (170, 170, 170),

        1
    )


    y += 20


    if ree_elements:

        for element, level in ree_elements.items():

            text = (
                f"{element}: {level}"
            )

            cv2.putText(

                frame,

                text[:31],

                (x, y),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.37,

                (255, 255, 255),

                1
            )

            y += 20

            if y > h - 30:

                break

    else:

        cv2.putText(

            frame,

            "No known REEs",

            (x, y),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.38,

            (180, 180, 180),

            1
        )

        y += 20


    # --------------------------------------------------------
    # INTERNET STATUS
    # --------------------------------------------------------

    y = min(
        y + 10,
        h - 45
    )


    cv2.putText(

        frame,

        "KNOWLEDGE SOURCE",

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.37,

        (170, 170, 170),

        1
    )


    y += 18


    status = web_data["status"]

    cv2.putText(

        frame,

        status[:30],

        (x, y),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.35,

        (220, 220, 220),

        1
    )


    # --------------------------------------------------------
    # SHOW
    # --------------------------------------------------------

    cv2.imshow(
        WINDOW_NAME,
        frame
    )


    # --------------------------------------------------------
    # QUIT
    # --------------------------------------------------------

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

camera.release()

cv2.destroyAllWindows()

print()
print("Program stopped.")