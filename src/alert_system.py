import os
import cv2
import threading
import winsound
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from src.rest_area_service import DrowsyShelterService

load_dotenv()

FONT_PATH = "assets/fonts/NotoSansKR-VariableFont_wght.ttf"

class AlertSystem:
    def __init__(self, alarm=30):
        self.danger_count = 0
        self.alarm = alarm
        self.is_alarming = False
        self.was_danger = False
        self.nearest_shelters = []
        self.drowsy_count = 0

        try:
            self.current_lat = float(os.getenv("DEFAULT_LAT", "37.4979"))
            self.current_lng = float(os.getenv("DEFAULT_LNG", "127.0276"))
            self.shelter_service = DrowsyShelterService()
        except ValueError as e:
            print(f"[경고] {e} — 졸음쉼터 기능 비활성화")
            self.shelter_service = None

    def play_sound(self):
        winsound.Beep(2500, 500)
        self.is_alarming = False

    def _draw_korean_text(self, frame, text, pos, font_size=18, color=(255, 255, 255)):
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        font = ImageFont.truetype(FONT_PATH, font_size)
        draw.text(pos, text, font=font, fill=(color[2], color[1], color[0]))
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def _draw_shelter_info(self, frame):
        if not self.nearest_shelters:
            return frame
        height, width = frame.shape[:2]
        panel_h = 35 + len(self.nearest_shelters) * 30
        panel_y = height - panel_h - 10
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, panel_y), (width - 10, height - 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        frame = self._draw_korean_text(frame, "[ 가까운 졸음쉼터 ]",
                                       (20, panel_y + 5), font_size=18, color=(0, 255, 255))

        for i, s in enumerate(self.nearest_shelters):
            name = s.get("name") or "이름 없음"
            dist = s.get("distance_km", 0)
            direction = s.get("direction") or ""
            road = s.get("road_name") or ""
            text = f"{i+1}. {name}  ({road} {direction})  {dist:.1f}km"
            y = panel_y + 5 + (i + 1) * 30
            frame = self._draw_korean_text(frame, text, (20, y), font_size=16, color=(255, 255, 255))

        return frame

    def process_frame(self, frame, is_drowsy, is_distracted):
        height, width = frame.shape[:2]

        if is_drowsy or is_distracted:
            self.danger_count += 1
        else:
            self.danger_count = max(0, self.danger_count - 1)

        if is_drowsy:
            self.drowsy_count += 1
        else:
            self.drowsy_count = max(0, self.drowsy_count - 1)

        is_danger = self.danger_count > self.alarm

        if 5 < self.danger_count <= self.alarm:
            cv2.rectangle(frame, (0, 0), (width, height), (0, 255, 255), 10)
            status_text = "CAUTION: "
            if is_drowsy: status_text += "DROWSY "
            if is_distracted: status_text += "DISTRACTED"
            cv2.putText(frame, status_text, (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

        elif is_danger:
            cv2.rectangle(frame, (0, 0), (width, height), (0, 0, 255), 20)
            cv2.putText(frame, "DANGER", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 4)

            if not self.is_alarming:
                self.is_alarming = True
                threading.Thread(target=self.play_sound, daemon=True).start()

            if not self.was_danger and self.shelter_service and self.drowsy_count > self.alarm:
                self.nearest_shelters = self.shelter_service.find_nearest(
                    self.current_lat, self.current_lng, limit=3
                )

            frame = self._draw_shelter_info(frame)

        else:
            self.nearest_shelters = []

        self.was_danger = is_danger
        return frame
