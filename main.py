from ultralytics import YOLO
import numpy as np
import os
import cv2

from src.alert_system import AlertSystem

'''
def main():
    model_path = "model/eyesyawn.pt"
    
    if not os.path.exists(model_path):
        print(f"{model_path} 경로에 모델 파일이 없습니다.")
        return

    # 2. 모델 로드
    model = YOLO(model_path)

    results = model.predict(
        source="data/test/images",
        save=True,                 
        conf=0.25,                 
        line_width=2               
    )

if __name__ == "__main__":
    main()
    '''
    
def preprocess_frame_opencv(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)

    if mean_brightness < 50:
        gamma = 2.0
    elif mean_brightness < 90:
        gamma = 1.5
    else:
        gamma = 1.0
    if gamma == 1.0:
        return frame
    invGamma = 1.0 / gamma

    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    processed_frame = cv2.LUT(frame, table)
    
    return processed_frame



def main():
    model = YOLO("model/eyesyawn.pt")
    
    cap = cv2.VideoCapture(0)

    alert_system = AlertSystem(alarm=30)
    DROWSY_CLASS_ID = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        processed_frame = preprocess_frame_opencv(frame)

        results = model.predict(processed_frame, conf=0.25, verbose=False)
        annotated = results[0].plot()

        detected_classes = results[0].boxes.cls.cpu().numpy()
        sleep_OX = DROWSY_CLASS_ID in detected_classes

        annotated = alert_system.process_frame(annotated, sleep_OX)

        cv2.imshow("Detection", annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):  # q로 종료!!
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

