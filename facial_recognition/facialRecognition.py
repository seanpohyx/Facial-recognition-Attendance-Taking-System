import numpy as np
import cv2
# import pickle
import os
import errno
from datetime import datetime
from .constants import CONST_YML_FILE, CONST_VIDEO_NAME, CONST_THICKNESS, \
    CONST_FACECASCADE, CONST_CONF_STANDARD, CONST_COLOR, CONST_SCALE_FACTOR, CONST_MIN_NEIGHBORS, \
    CONST_MINSIZE, BASE_DIR
import threading
from .classifier import train_classifer

def markAttendanceCam(students_data, Attend, session):
    """Video streaming generator function."""
    stroke = 2
    classifier = cv2.CascadeClassifier(CONST_FACECASCADE)
    clf = cv2.face.LBPHFaceRecognizer_create()
    #need check if const_yml file exist
    clf.read(CONST_YML_FILE)
    video = cv2.VideoCapture(0)
    students_dict = getStudentData(students_data)
    class_id = students_data[0][1].classId

    if not video.isOpened():
        raise RuntimeError('Could not start camera.')

    while video.isOpened():
        _, img = video.read()
        # img = recognise(img, clf, classifier)
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # detecting features in gray-scale image, returns coordinates, width and height of features
        features = classifier.detectMultiScale(
            gray_img,
            scaleFactor=CONST_SCALE_FACTOR,
            minNeighbors=CONST_MIN_NEIGHBORS,
            minSize=CONST_MINSIZE)

        # drawing rectangle around the feature and labeling it
        for (x, y, w, h) in features:
            _id, conf = clf.predict(gray_img[y:y + h, x:x + w])
            print(conf)
            if _id in students_dict and conf < CONST_CONF_STANDARD:
                print(students_dict[_id])
                if students_dict[_id][1] is False:
                    students_dict[_id][1] = True
                    attend_data = Attend.query.filter_by(studentId=_id) \
                                .filter(Attend.classId == class_id) \
                                .order_by(Attend.id.desc()).first()
                    attend_data.attendance = True
                    attend_data.datetime = datetime.now()
                    print(attend_data)
                    session.commit()
                    # p1 = multiprocessing.Process(target=updateDatabaseAttendence, args=(Attend, _id, session, class_id))
                    # p1.start()
                else:
                    #user recognised and marked
                    cv2.rectangle(img, (x, y), (x + w, y + h), CONST_COLOR["green"], stroke)
                    cv2.putText(img, students_dict[_id][0], (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.8, CONST_COLOR["green"],
                                CONST_THICKNESS, cv2.LINE_AA)

            else:
                cv2.rectangle(img, (x, y), (x + w, y + h), CONST_COLOR["white"], stroke)
                # cv2.putText(img, "no one", (x, y-4), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1, cv2.LINE_AA)
                print("unidentified")

        cv2.imwrite(CONST_VIDEO_NAME, img)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open(CONST_VIDEO_NAME, 'rb').read() + b'\r\n')

def registerFaceCam(student, student_model):
    """Video streaming generator function."""
    classifier = cv2.CascadeClassifier(CONST_FACECASCADE)
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read(CONST_YML_FILE)
    video = cv2.VideoCapture(0)
    image_taken = 0
    stroke = 2
    isClassified = False

    if not video.isOpened():
        raise RuntimeError('Could not start camera.')

    while video.isOpened():
        _, img = video.read()
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # detecting features in gray-scale image, returns coordinates, width and height of features
        features = classifier.detectMultiScale(
            gray_img,
            scaleFactor=CONST_SCALE_FACTOR,
            minNeighbors=CONST_MIN_NEIGHBORS,
            minSize=CONST_MINSIZE)

        # drawing rectangle around the feature and labeling it
        for (x, y, w, h) in features:

            # image, name', org, font, fontScale, color, thickness, cv2.LINE_AA)


            if(image_taken < 100):
                cv2.rectangle(img, (x, y), (x + w, y + h), CONST_COLOR["white"], stroke)
                cv2.putText(img, "UPDATING FACE", (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.8, CONST_COLOR["white"],
                            CONST_THICKNESS, cv2.LINE_AA)
                image_taken += 1
                roi_img = gray_img[y:y+h, x:x+w]
                folder = student.name
                roi_img = cv2.resize(roi_img, (400, 400))
                # generateDataSet(roi_img, folder, image_taken)
                p1 = threading.Thread(target=generateDataSet, args=(roi_img, folder, image_taken))
                p1.start()
            else:
                cv2.rectangle(img, (x, y), (x + w, y + h), CONST_COLOR["green"], stroke)
                cv2.putText(img, "COMPLETE", (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.8, CONST_COLOR["white"],
                            CONST_THICKNESS, cv2.LINE_AA)

                if not isClassified:
                    t1 = threading.Thread(target=train_classifer, args=[student_model])
                    t1.start()
                    isClassified = True


        cv2.imwrite(CONST_VIDEO_NAME, img)

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open(CONST_VIDEO_NAME, 'rb').read() + b'\r\n')


def updateDatabaseAttendence(Attend, id, session, class_id):
    # attend_data = Attend.query.filter_by(studentId=id, closedate = None, ).first()

    attend_data = Attend.query.filter_by(studentId=id) \
                .filter(Attend.classId == class_id) \
                .order_by(Attend.id.desc()).first()
    attend_data.attendance = True
    attend_data.datetime = datetime.now()
    session.commit()
    print("Attendance Updated", 'Success')


def generateDataSet(img, folder, img_id):
    # Create directory
    image_dir = os.path.join(BASE_DIR, "studentsData")
    try:
        # Create target Directory 
        # makedirs will create the required subdirectories, whereas mkdir can only create one directory.
        os.makedirs(image_dir + '/' + folder)
        print("Directory ", folder, " Created ")
        cv2.imwrite(image_dir + '/' +folder+"/"+folder+"-"+str(img_id)+".jpg", img)
    except OSError as e:
        if e.errno == errno.EEXIST:
            # print('Directory already exist.')
            cv2.imwrite(image_dir + '/' +folder+"/"+folder+"-"+str(img_id)+".jpg", img)
        else:
            raise


def getStudentData(students):
    # with open(CONST_LABEL_PICKLE, 'rb') as f:
    #     student_data = pickle.load(f)
    results = {}

    for student in students:
        results[student[0].id] = [student[0].name, student[1].attendance]

    return results

# def markAttendanceCam1():
#     """Video streaming generator function."""
#     classifier = cv2.CascadeClassifier(CONST_FACECASCADE)
#     clf = cv2.face.LBPHFaceRecognizer_create()
#     clf.read(CONST_YML_FILE)
#     video = cv2.VideoCapture(0)
#
#     while video.isOpened():
#         _, img = video.read()
#         img = recognise(img, clf, classifier)
#         cv2.imwrite(CONST_VIDEO_NAME, img)
#
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + open(CONST_VIDEO_NAME, 'rb').read() + b'\r\n')
#
# def registerFaceCam1():
#     """Video streaming generator function."""
#     classifier = cv2.CascadeClassifier(CONST_FACECASCADE)
#     clf = cv2.face.LBPHFaceRecognizer_create()
#     clf.read(CONST_YML_FILE)
#     video = cv2.VideoCapture(0)
#     image_taken = 0
#
#     if not video.isOpened():
#         raise RuntimeError('Could not start camera.')
#
#     while video.isOpened():
#         _, img = video.read()
#
#         if(image_taken < 100):
#             count, img = captureFace(img, classifier, image_taken, clf)
#             image_taken += count
#         else:
#             img = recognise(img, clf, classifier)
#         cv2.imwrite(CONST_VIDEO_NAME, img)
#
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + open(CONST_VIDEO_NAME, 'rb').read() + b'\r\n')
#
#
# def recognise(img, clf, classifier):
#
#     # coords = drawBoundaries(img, classifier, clf)
#     drawBoundaries(img, classifier, clf)
#     return img


# def drawBoundaries(img, classifier, clf):
#
#     stroke = 2
#     conf = 100
#     gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     # detecting features in gray-scale image, returns coordinates, width and height of features
#     features = classifier.detectMultiScale(
#         gray_img,
#         scaleFactor=CONST_SCALE_FACTOR,
#         minNeighbors=CONST_MIN_NEIGHBORS,
#         minSize=CONST_MINSIZE)
#     coords = []
#     labels = getStudentData()
#
#     # drawing rectangle around the feature and labeling it
#     for (x, y, w, h) in features:
#
#         roi_gray = gray_img[y:y+h, x:x+w]
#         # roi_color = img[y:y+h, x:x+w]
#         # Predicting the id of the user
#
#         id, conf = clf.predict(roi_gray)
#         print(conf)
#         if conf < CONST_CONST_STANDARD:
#             print(id)
#             print(labels[id])
#             # image, name', org, font, fontScale, color, thickness, cv2.LINE_AA)
#             cv2.rectangle(img, (x,y), (x+w, y+h), CONST_COLOR["white"], stroke)
#             cv2.putText(img, labels[id], (x, y-4), cv2.FONT_HERSHEY_SIMPLEX, 0.8, CONST_COLOR["white"], CONST_THICKNESS, cv2.LINE_AA)
#         else:
#             cv2.rectangle(img, (x,y), (x+w, y+h), CONST_COLOR["red"], stroke)
#             print("no one")
#             #cv2.putText(img, "no one", (x, y-4), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1, cv2.LINE_AA)
#
#         coords = [x, y, w, h]
#
#     if conf < 40:
#         return coords
#     else:
#         return 0
#
# def captureFace(img, classifier, img_id, clf):
#     coords = drawBoundaries(img, classifier, clf)
#     count = 0
#     print(coords)
#     if coords != 0 and len(coords) == 4:
#         count += 1
#         gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         roi_img = gray_img[coords[1]:coords[1]+coords[3], coords[0]:coords[0]+coords[2]]
#         folder = "seannypoop"
#         roi_img = cv2.resize(roi_img, (400, 400))
#         generateDataSet(roi_img, folder, img_id)
#
#     return count, img