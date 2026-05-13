from ultralytics import YOLO
import os
import cv2

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
    
    

#<실시간 영상>


def main():
    model = YOLO("model/eyesyawn.pt")
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        results = model.predict(frame, conf=0.25, verbose=False)
        annotated = results[0].plot()
        
        cv2.imshow("Detection", annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):  # q로 종료!!
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

