import cv2
import colorsys

# ============================================================
# REE VISIBLE EMISSION DATABASE
# Wavelengths are representative emission peaks in nm
# ============================================================

REE_DATABASE = {

    "Eu3+": {
        "peaks": [590, 613],
        "description": "Orange / Red emission"
    },

    "Tb3+": {
        "peaks": [490, 545, 590, 624],
        "description": "Green emission"
    },

    "Dy3+": {
        "peaks": [478, 489, 575, 578, 650],
        "description": "Blue / Yellow / Red emission"
    },

    "Sm3+": {
        "peaks": [567, 600, 647],
        "description": "Orange / Red emission"
    },

    "Pr3+": {
        "peaks": [480, 500, 614, 641, 650],
        "description": "Blue / Green / Red emission"
    },

    "Er3+": {
        "peaks": [520, 530, 545],
        "description": "Green emission"
    },

    "Ho3+": {
        "peaks": [464, 475, 492, 505],
        "description": "Blue / Green emission"
    },

    "Ce3+": {
        "peaks": [420],
        "description": "Blue emission"
    }
}


# ============================================================
# RGB -> APPROXIMATE WAVELENGTH
# ============================================================

def rgb_to_wavelength(r, g, b):

    # Normalize
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    maximum = max(r_norm, g_norm, b_norm)
    minimum = min(r_norm, g_norm, b_norm)

    # Very dark image
    if maximum < 0.12:
        return None, "No significant visible light"

    # Convert RGB to HSV
    h, s, v = colorsys.rgb_to_hsv(
        r_norm,
        g_norm,
        b_norm
    )

    hue = h * 360

    # Low saturation means white/grey light
    if s < 0.15:
        return None, "White / mixed light"

    # Approximate wavelength mapping
    if hue < 30:
        wavelength = 620 + (hue / 30) * 10
        color = "Red"

    elif hue < 60:
        wavelength = 590 + ((hue - 30) / 30) * 30
        color = "Orange / Yellow"

    elif hue < 120:
        wavelength = 520 + ((hue - 60) / 60) * 50
        color = "Green"

    elif hue < 180:
        wavelength = 450 + ((hue - 120) / 60) * 70
        color = "Blue"

    elif hue < 240:
        wavelength = 400 + ((hue - 180) / 60) * 50
        color = "Violet / Blue"

    else:
        wavelength = 620
        color = "Red"

    return int(wavelength), color


# ============================================================
# FIND PROBABLE REEs
# ============================================================

def identify_ree(wavelength):

    if wavelength is None:
        return []

    results = []

    for ree, data in REE_DATABASE.items():

        peaks = data["peaks"]

        # Find closest emission peak
        closest_peak = min(
            peaks,
            key=lambda x: abs(x - wavelength)
        )

        difference = abs(closest_peak - wavelength)

        # ----------------------------------------------------
        # Tolerance
        #
        # Webcam wavelength estimation is NOT spectrometer
        # precision, so use a relatively broad tolerance.
        # ----------------------------------------------------

        tolerance = 15

        if difference <= tolerance:

            # Convert difference to rough score
            confidence = 100 - (difference / tolerance) * 100

            results.append(
                (
                    ree,
                    closest_peak,
                    difference,
                    confidence
                )
            )

    # Highest confidence first
    results.sort(
        key=lambda x: x[3],
        reverse=True
    )

    return results


# ============================================================
# START WEBCAM
# ============================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("ERROR: Could not open webcam.")
    exit()

print("Webcam started.")
print("Place the light-emitting sample in the center.")
print("Press Q to quit.")


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read webcam.")
        break

    height, width, _ = frame.shape

    # --------------------------------------------------------
    # Central detection area
    # --------------------------------------------------------

    box_size = 150

    x1 = width // 2 - box_size // 2
    x2 = width // 2 + box_size // 2

    y1 = height // 2 - box_size // 2
    y2 = height // 2 + box_size // 2

    roi = frame[y1:y2, x1:x2]

    # --------------------------------------------------------
    # OpenCV gives BGR
    # --------------------------------------------------------

    b, g, r = cv2.mean(roi)[:3]

    r = int(r)
    g = int(g)
    b = int(b)

    # --------------------------------------------------------
    # Convert RGB -> wavelength
    # --------------------------------------------------------

    wavelength, color = rgb_to_wavelength(r, g, b)

    # --------------------------------------------------------
    # Draw detection box
    # --------------------------------------------------------

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        (255, 255, 255),
        2
    )

    # --------------------------------------------------------
    # Display RGB
    # --------------------------------------------------------

    cv2.putText(
        frame,
        f"RGB: ({r}, {g}, {b})",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    # --------------------------------------------------------
    # Display wavelength
    # --------------------------------------------------------

    if wavelength is not None:

        cv2.putText(
            frame,
            f"Estimated wavelength: {wavelength} nm",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Visible color: {color}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        # ----------------------------------------------------
        # Identify probable REEs
        # ----------------------------------------------------

        results = identify_ree(wavelength)

        if len(results) > 0:

            cv2.putText(
                frame,
                "Probable REE:",
                (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            # Show top 3 candidates
            for i, result in enumerate(results[:3]):

                ree = result[0]
                peak = result[1]
                difference = result[2]
                confidence = result[3]

                text = (
                    f"{ree} | peak {peak} nm | "
                    f"match {confidence:.0f}%"
                )

                cv2.putText(
                    frame,
                    text,
                    (20, 180 + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    2
                )

        else:

            cv2.putText(
                frame,
                "No strong REE spectral match",
                (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

    else:

        cv2.putText(
            frame,
            color,
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

    # --------------------------------------------------------
    # Display webcam
    # --------------------------------------------------------

    cv2.imshow(
        "REE Visible Spectrum Detector",
        frame
    )

    # Q = quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()
cv2.destroyAllWindows()