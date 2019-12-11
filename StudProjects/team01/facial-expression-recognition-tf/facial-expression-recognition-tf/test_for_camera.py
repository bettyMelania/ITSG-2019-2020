from keras.preprocessing.image import img_to_array
import imutils
import cv2
from keras.models import load_model
import numpy as np
import tensorflow as tf
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pafy


# parameters for loading data and images
detection_model_path = 'haarcascade_files/haarcascade_frontalface_default.xml'
emotion_model_path = 'models/_mini_XCEPTION.97-0.65.hdf5'

# hyper-parameters for bounding boxes shape
# loading models
face_detection = cv2.CascadeClassifier(detection_model_path)
#emotion_classifier = load_model(emotion_model_path, compile=False)
interpreter = tf.lite.Interpreter(model_path="models/model.tflite")
interpreter.allocate_tensors()
EMOTIONS = ["angry" ,"disgust","scared", "happy", "sad", "surprised",
 "neutral"]

def initial_emotions_count():
    return {
        "angry": 0 ,
        "disgust": 0,
        "scared": 0, 
        "happy": 0, 
        "sad": 0, 
        "surprised": 0,
        "neutral": 1
    }

emotions_count = initial_emotions_count()

acting_mirror_window_name = 'Acting Mirror'
graph_window_name = 'Graph for Person 0'
details_window_name = 'Emotions for Person 0'

app_state = type('obj', (object,), {
    'show_graph': False,
    'show_details': False,
    'show_rectangles': True
})

def update_graph_data():
    all_emotions_count = list(emotions_count.values())
    total_emotions = sum(all_emotions_count)
    percentage_emotions = [x / total_emotions * 100 for x in all_emotions_count]

    ax1.clear()
    ax1.bar(list(emotions_count.keys()), percentage_emotions)

# starting video streaming
fig = plt.figure()
ax1 = fig.add_subplot(111, projection='polar')
update_graph_data()

cv2.namedWindow(acting_mirror_window_name)
out = cv2.VideoWriter('output.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (800,600))
#camera = cv2.VideoCapture(0)
#camera = cv2.VideoCapture('Derren.Brown.Miracle.2018.1080p.NF.WEB-DL.DD+2.0.H.264-SiGMA.mkv')

url = 'https://www.youtube.com/watch?v=zgqz8Je7P0s'
vPafy = pafy.new(url)
play = vPafy.getbest(preftype="webm")

camera = cv2.VideoCapture(play.url)
while camera.isOpened():
    frame = camera.read()[1]
    #reading the frame
    frame = imutils.resize(frame,width=800)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detection.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(30,30),flags=cv2.CASCADE_SCALE_IMAGE)
    faces = sorted(faces, reverse=True,
        key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))

    canvas = np.zeros((250, 300, 3), dtype="uint8")
    frameClone = frame.copy()

    for index in range(len(faces)):
        (fX, fY, fW, fH) = faces[index]
        # Extract the ROI of the face from the grayscale image, resize it to a fixed 48x48 pixels, and then prepare
        # the ROI for classification via the CNN
        roi = gray[fY:fY + fH, fX:fX + fW]
        roi = cv2.resize(roi, (48, 48))
        roi = roi.astype("float") / 255.0
        roi = img_to_array(roi)
        roi = np.expand_dims(roi, axis=0)
        
        #preds = emotion_classifier.predict(roi)[0]
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        interpreter.set_tensor(input_details[0]['index'], roi)
        interpreter.invoke()
        preds = interpreter.get_tensor(output_details[0]['index'])[0]
        emotion_probability = np.max(preds)
        label = EMOTIONS[preds.argmax()]

        for (i, (emotion, prob)) in enumerate(zip(EMOTIONS, preds)):
            #if index == 0: 
            #    emotions_count[label] += 1
            
            #if index == 0:
            #    # construct the label text
            #    text = "{}: {:.2f}%".format(emotion, prob * 100)
            #    w = int(prob * 300)
            #    cv2.rectangle(canvas, (7, (i * 35) + 5),
            #    (w, (i * 35) + 35), (0, 0, 255), -1)
            #    cv2.putText(canvas, text, (10, (i * 35) + 23),
            #    cv2.FONT_HERSHEY_SIMPLEX, 0.45,
            #    (255, 255, 255), 2)
            
            if app_state.show_rectangles:
                # construct the rectangle frames for persons
                #if index == 0:
                if index == -1:
                    cv2.putText(frameClone, 'person {} is {}'.format(index, label), (fX, fY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
                else:
                    cv2.putText(frameClone, label, (fX, fY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
                cv2.rectangle(frameClone, (fX, fY), (fX + fW, fY + fH),
                                (0, 0, 255), 2)

    cv2.imshow(acting_mirror_window_name, frameClone)
    outputFrame = cv2.resize(frameClone, (800,600), interpolation = cv2.INTER_AREA)
    out.write(outputFrame)
    
    if app_state.show_details:
        cv2.imshow(details_window_name, canvas)
    
    if app_state.show_graph == True:
        update_graph_data()

        fig.canvas.draw()
        img = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8,sep='')
        img  = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        # img is rgb, convert to opencv's default bgr
        img = cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
        # display image with opencv or any operation you like
        cv2.imshow(graph_window_name,img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    #if cv2.waitKey(16) & 0xFF == ord('g'):
    #    app_state.show_graph = not app_state.show_graph
    #    if app_state.show_graph == False:
    #        cv2.destroyWindow(graph_window_name)
    #if cv2.waitKey(16) & 0xFF == ord('d'):
    #    app_state.show_details = not app_state.show_details
    #    if app_state.show_details == False:
    #        cv2.destroyWindow(details_window_name)
    #if cv2.waitKey(16) & 0xFF == ord('n'):
    #    app_state.show_rectangles = not app_state.show_rectangles

camera.release()
out.release()
cv2.destroyAllWindows()
