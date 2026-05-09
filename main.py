from ultralytics import YOLO
import os

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