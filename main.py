import cv2
import numpy as np
from ultralytics import YOLO
from src.alert_system import AlertSystem


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
    return cv2.LUT(frame, table)


def main():
    drowsy_model = YOLO("model/eyesyawn.pt")
    distract_model = YOLO("model/distract.pt")

    cap = cv2.VideoCapture(0)
    alert_system = AlertSystem(alarm=30)
    DROWSY_CLASS_ID = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        processed_frame = preprocess_frame_opencv(frame)

        drowsy_results = drowsy_model.predict(processed_frame, conf=0.25, verbose=False)
        distract_results = distract_model.predict(processed_frame, conf=0.25, classes=[2, 3, 4], verbose=False)

        is_drowsy = False
        is_distracted = False

        for r in drowsy_results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                if cls_id == DROWSY_CLASS_ID:
                    is_drowsy = True
                label = f"{drowsy_model.names[cls_id]} {conf:.2f}"
                cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (255, 0, 0), 2)
                cv2.putText(frame, label, (xyxy[0], xyxy[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        for r in distract_results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                if conf >= 0.50:
                    if cls_id in [2, 3]:
                        is_distracted = True
                    label = f"{distract_model.names[cls_id]} {conf:.2f}"
                    cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 255, 0), 2)
                    cv2.putText(frame, label, (xyxy[0], xyxy[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        frame = alert_system.process_frame(frame, is_drowsy, is_distracted)

        cv2.imshow("Driver Monitor System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
