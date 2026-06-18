import cv2


class CameraService:

    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)

    def capture_frame(self):
        return self.cap.read()

    def release(self):
        self.cap.release()