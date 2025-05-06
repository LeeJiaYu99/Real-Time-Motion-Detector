import cv2
import base64
import os
import json

from kafka import KafkaProducer
from kafka.errors import KafkaError

class FrameCapturer:
    def __init__(self, cam_id, video_path, kafka_server, kafka_topic):
        self.cam_id = cam_id    
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        # self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        # self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.frame_count = 0
        self.running = True

        self.kafka_topic = kafka_topic
        self.producer = KafkaProducer(bootstrap_servers=[kafka_server])

    @staticmethod
    def producer_report(err,msg):
        """Delivery report callback, logs message status."""
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivery to{msg.topic()} [{msg.partition()}]")

    @staticmethod
    def on_send_success(record_metadata):
        """Callback for successful message delivery."""
        print(f"Message delivered to {record_metadata.topic} partition {record_metadata.partition}")

    @staticmethod
    def on_send_error(excp):
        """Callback for failed message delivery."""
        print(f"Failed to send message: {excp}")

    @staticmethod
    def encode_frame(frame):
        """Convert frame to format that is easily transfered and stored in kafka server"""
        ## Resize frame
        # frame = cv2.resize(frame, (int(self.width/4), int(self.height/4)))

        # Encode the frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

        # Base64 encode to JPEG buffer to bytes
        frame_b64 = base64.b64encode(buffer).decode('utf-8')

        return frame_b64
    
    def collect_frame(self, partition):
        """Capture frames and push to kafka"""
        print("Starting frame collection...")
        prev_frame_b64 = None

        while self.cap.isOpened():
            success, frame = self.cap.read()
            if not success:
                print("Failed to capture frame. Exiting...")
                break

            # Collect every 10 frames of the stream
            if self.frame_count % 10 == 0 and prev_frame_b64 is not None:
                prev_frame_b64 = self.encode_frame(frame)

                # Each message contains two frames, the previous and current frames
                message = {
                    'prev_frame': prev_frame_b64,
                    'curr_frame': frame_b64
                }

                # Serialize the message and encode to bytes
                message_bytes = json.dumps(message).encode('utf-8')

                # Optional: Splitting data into different partitions
                if self.frame_count % 20 == 0:
                    partition_no = partition + 4
                    future = self.producer.send(self.kafka_topic, partition=partition_no, key=str(self.cam_id).encode('utf-8'), value=message_bytes).add_callback(self.on_send_success).add_errback(self.on_send_error)
                else:
                    future = self.producer.send(self.kafka_topic, partition=partition, key=str(self.cam_id).encode('utf-8'), value=message_bytes).add_callback(self.on_send_success).add_errback(self.on_send_error)

                try:
                    future.get(timeout=10)
                except KafkaError as e:
                    print(f"Kafka error: {e}")

            # Encode one frame first upon starting of the system
            if self.frame_count == 0:
                frame_b64 = self.encode_frame(frame)

            self.frame_count += 1
            prev_frame_b64 = frame_b64

        self.cap.release()
        self.producer.flush()
        self.producer.close()
        self.running = False
        print("Exiting frame collection...")

def main():
    # load configuration and environment
    cam_id = int(os.getenv("CAM_ID", 18))
    config_path = os.gentev("CONFIG_PATH", "config.json")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        return
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {e}")
        return   

    # Get the configuration of the relevant camera
    cam_config = next((cam for cam in config["cams"] if cam["cam_id"] == cam_id), None) 

    if not cam_config:
        print(f"No configuration found for cam ID {cam_id}")
        return
    
    kafka_server = cam_config["kafka_server"]
    kafka_topic = cam_config["kafka_topic"]
    video_path = cam_config["video_path"]
    partition = cam_config["partition"]

    # Start the system
    cam1 = FrameCapturer(cam_id, video_path, kafka_server, kafka_topic)
    cam1.collect_frame(partition)

if __name__ == "__main__":
    main()