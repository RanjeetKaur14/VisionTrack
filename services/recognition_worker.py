import threading
import queue


class RecognitionWorker:

    def __init__(self, process_function):

        self.queue = queue.Queue()

        self.process_function = process_function

        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )

        self.thread.start()

    def add_job(self, data):

        if self.queue.qsize() > 0:

            print(
                "JOB SKIPPED - WORKER BUSY"
            )

            return

        self.queue.put(data)

        print(
            "QUEUE SIZE:",
            self.queue.qsize()
        )

    def run(self):

        while True:

            data = self.queue.get()

            try:

                self.process_function(data)

            except Exception as e:

                print(
                    "WORKER ERROR:",
                    e
                )

            self.queue.task_done()