import numpy as np
from PIL import Image
import os, cv2
# import pickle
from .constants import CONST_FACECASCADE, CONST_YML_FILE, CONST_MIN_NEIGHBORS, CONST_SCALE_FACTOR

def train_classifer(Students):
    # Read all the images in custom data-set
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.join(BASE_DIR, "studentsData")
    face_cascade = cv2.CascadeClassifier(CONST_FACECASCADE)
    recogniser = cv2.face.LBPHFaceRecognizer_create()

    student_dict ={}
    y_labels = []
    x_train = []

    for root, dirs, files in os.walk(image_dir):
        name = os.path.basename(root)
        print(name)
        student = Students.query\
            .filter(Students.name == name)\
            .first()
        print(student)
        print("here")

        # filename = name.replace(" ", "-").lower()
        for file in files:
            if file.endswith("png") or file.endswith("jpg"):
                path = os.path.join(root, file)
                #might need to change
                if(student is not None ):

                    print("loop item")
                    student_dict[name] = student.id
                    print(student_dict)

                    pil_image = Image.open(path).convert("L")
                    image_array = np.array(pil_image, "uint8")

                    # faces = face_cascade.detectMultiScale(image_array, scaleFactor=1.5, minNeighbors=5)
                    faces = face_cascade.detectMultiScale(image_array, scaleFactor=CONST_SCALE_FACTOR, minNeighbors=CONST_MIN_NEIGHBORS)
                    # print(image_array)

                    for (x,y,w,h) in faces:
                        roi = image_array[y:y+h, x:x+w]
                        x_train.append(roi)
                        y_labels.append(student.id)



    # with open(CONST_LABEL_PICKLE, "wb") as f:
    #     pickle.dump(student_dict, f)

    recogniser.train(x_train, np.array(y_labels))
    recogniser.save(CONST_YML_FILE)
    print("done classifying")
    # return "classified"
