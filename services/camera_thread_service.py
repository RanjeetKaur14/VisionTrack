import cv2
import threading


class CameraThreadService:

    def __init__(self):

        self.cap = cv2.VideoCapture(0)

        self.frame = None

        self.running = True

        self.lock = threading.Lock()

        self.thread = threading.Thread(
            target=self.update,
            daemon=True
        )

        self.thread.start()

    def update(self):

        while self.running:

            ret, frame = self.cap.read()

            if ret:

                with self.lock:

                    self.frame = frame.copy()

    def get_frame(self):

        with self.lock:

            if self.frame is None:
                return None

            return self.frame.copy()

    def release(self):

        self.running = False

        self.thread.join()

        self.cap.release()