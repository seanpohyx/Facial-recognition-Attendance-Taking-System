import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONST_FACECASCADE = os.path.join(BASE_DIR, "haarcascade_frontalface_default.xml")
CONST_YML_FILE = os.path.join(BASE_DIR, "trainer.yml")
CONST_VIDEO_NAME = os.path.join(BASE_DIR, "live.jpg")
# CONST_LABEL_PICKLE = os.path.join(BASE_DIR,'label.pickle')
CONST_COLOR = {"blue": (255, 0, 0), "red": (0, 0, 255), "green": (0, 255, 0), "white": (255, 255, 255)}
CONST_SCALE_FACTOR = 1.2
CONST_MIN_NEIGHBORS = 5
CONST_THICKNESS = 2
CONST_MINSIZE = (150, 150)
CONST_CONF_STANDARD = 30