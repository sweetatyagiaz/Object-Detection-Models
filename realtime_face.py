import os

# Force the system GUI to hook into the highly stable X11 compatibility layer
os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2
import time
import multiprocessing as mp
from multiprocessing import Process, Queue
import queue as pyqueue

# 1. Configuration
DATABASE_DIR = "/home/rakesh/GitRepo/Object-Detection-Models/database/"
DISTANCE_THRESHOLD = 0.60
NUM_WORKERS = max(1, (os.cpu_count() or 4) - 1)   # leave one core for capture/display
TASK_QUEUE_MAXSIZE = NUM_WORKERS * 2               # allow a small amount of in-flight work


def recognition_worker(task_q: Queue, result_q: Queue, db_path: str, threshold: float):
    """
    Runs in its own OS process. Each process imports DeepFace and builds/loads
    the recognition model ONCE, then keeps pulling frames off the shared task
    queue. Using separate processes (instead of threads) gives real parallel
    execution across CPU cores, since DeepFace/TensorFlow's Python-level model
    objects aren't safely shared across threads and TF inference doesn't
    reliably release the GIL for pure-Python thread parallelism.
    """
    from deepface import DeepFace  # import inside the process (must happen after fork/spawn)

    # Warm up the model once so the first real frame isn't slow, and so any
    # load-time race conditions happen here instead of mid-stream.
    try:
        DeepFace.build_model("Facenet512")
    except Exception as e:
        print(f"[worker {os.getpid()}] model warmup warning: {e}")

    while True:
        item = task_q.get()
        if item is None:  # sentinel -> shut down
            break

        frame_id, frame = item

        try:
            results = DeepFace.find(
                img_path=frame,
                db_path=db_path,
                model_name="Facenet512",
                detector_backend="yunet",
                enforce_detection=False,
                silent=True,
            )

            df = results if isinstance(results, list) else [results]
            df = df[0] if len(df) > 0 else None

            payload = None
            if df is not None and not df.empty:
                valid_matches = df[df["distance"] < threshold]

                x = int(df.loc[0, "source_x"])
                y = int(df.loc[0, "source_y"])
                w = int(df.loc[0, "source_w"])
                h = int(df.loc[0, "source_h"])

                if not valid_matches.empty:
                    best_match = valid_matches.sort_values(by="distance", ascending=True).iloc[0]
                    person_name = os.path.basename(os.path.dirname(best_match["identity"]))
                    confidence = best_match["confidence"]
                    label = f"{person_name} ({confidence:.1f}%)"
                    color = (0, 255, 0)
                else:
                    label = "Unknown Person"
                    color = (0, 0, 255)

                payload = {"box": (x, y, w, h), "label": label, "color": color}

            result_q.put((frame_id, payload))

        except Exception as e:
            print(f"[worker {os.getpid()}] DeepFace warning: {e}")
            result_q.put((frame_id, None))


def main():
    task_q: Queue = mp.Queue(maxsize=TASK_QUEUE_MAXSIZE)
    result_q: Queue = mp.Queue()

    workers = []
    for _ in range(NUM_WORKERS):
        p = Process(
            target=recognition_worker,
            args=(task_q, result_q, DATABASE_DIR, DISTANCE_THRESHOLD),
            daemon=True,
        )
        p.start()
        workers.append(p)

    print(f"🧠 DeepFace AI process pool active ({NUM_WORKERS} workers, Facenet512 + YuNet).")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Error: Could not reach webcam interface frame.")
        return

    print("🎥 Real-time stream running at max hardware capacity. Press 'q' to close.")

    latest_recognition = None
    last_applied_frame_id = -1
    next_frame_id = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Only enqueue a new frame if there's room, so slow inference
            # naturally drops old frames instead of building up a backlog.
            try:
                task_q.put_nowait((next_frame_id, frame.copy()))
                next_frame_id += 1
            except pyqueue.Full:
                pass

            # Drain every available result, but only keep the one with the
            # highest frame_id -> guarantees we never show a stale overlay
            # that finished processing after a newer one already arrived.
            while True:
                try:
                    frame_id, payload = result_q.get_nowait()
                except pyqueue.Empty:
                    break
                if frame_id > last_applied_frame_id:
                    last_applied_frame_id = frame_id
                    latest_recognition = payload

            if latest_recognition is not None:
                x, y, w, h = latest_recognition["box"]
                lbl = latest_recognition["label"]
                clr = latest_recognition["color"]
                cv2.rectangle(frame, (x, y), (x + w, y + h), clr, 2)
                cv2.putText(frame, lbl, (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 0.6, clr, 1, cv2.LINE_AA)

            cv2.imshow("Zero-Lag Face Verification Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

        # Shut workers down cleanly
        for _ in workers:
            try:
                task_q.put_nowait(None)
            except pyqueue.Full:
                pass
        for p in workers:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()

        print("🎥 Framework shutdown clean.")


if __name__ == "__main__":
    # Required on platforms using 'spawn' (e.g. macOS/Windows) so child
    # processes don't re-run the capture loop.
    mp.set_start_method("spawn", force=False)
    main()