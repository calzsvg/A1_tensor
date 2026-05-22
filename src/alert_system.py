import cv2
import threading
import winsound

class AlertSystem:
    def __init__(self, alarm=30):
        self.sleep_count = 0
        self.alarm = alarm
        self.is_alarming = False

    def play_sound(self):
        winsound.Beep(2500, 500)
        self.is_alarming = False

    def process_frame(self, frame, sleep_OX):
        height, width = frame.shape[:2]

        if sleep_OX:
            self.sleep_count += 1
        else:
            self.sleep_count = max(0, self.sleep_count - 1)

        if 5 < self.sleep_count <= self.alarm:
            cv2.rectangle(frame, (0, 0), (width, height), (0, 255, 255), 10)
            cv2.putText(frame, "CAUTION", (30, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

        elif self.sleep_count > self.alarm:
            cv2.rectangle(frame, (0, 0), (width, height), (0, 0, 255), 20)
            cv2.putText(frame, "DANGER", (30, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 4)
            
            if not self.is_alarming:
                self.is_alarming = True
                threading.Thread(target=self.play_sound, daemon=True).start()

        return frame