import cv2
import numpy as np
import os
from kafka import KafkaConsumer
import json
import base64
from Cam import Cam

class FrameProcessor:
    def __init__(self):      
        self.config_path = os.getenv("CONFIG_PATH", "config.json")
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
                self.ftp_config = self.config['ftp']
                self.database_config = self.config['database']
                self.mail_config = self.config['mail']
                self.kafka_config = self.config['kafka']
        except FileNotFoundError:
            print(f"Configuration file not found: {self.config_path}")
            return
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}")
            return
        
        self.consumer = KafkaConsumer(self.kafka_config['topic'],
                                group_id=self.kafka_config['consumer_group'],
                                bootstrap_servers=self.kafka_config['server'],
                                auto_offset_reset='earliest',
                                value_deserrializer=lambda v: json.loads(v.decode('utf-8')),
                                key_deserializer=lambda k: k.decode('utf-8') if k else None
                                )
    
    def load_cam_config(self, key):
        cam_config = next((cam for cam in self.config["cams"] if cam["cam_id"] == key), None) 
        if not cam_config:
            print(f"No configuration found for cam ID {key}")
            return
        return cam_config
    
    @staticmethod
    def decode_frame(frame_b64):
        # Decode base64 string to bytes
        frame_bytes = base64.b64decode(frame_b64)
        # Convert bytes to numpy array and decode to frame
        frame = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        return frame
    
    def consume_frame(self):
        """Read a framw and process car tracking"""
        frame_count = 0
        while True:
            for message in self.consumer:
                frame_count += 1
                key = int(message.key)
                value = message.value
                # print(key, ": ", frame_count)
                cam_config = self.load_cam_config(key)

                # Import Cam class
                cam = Cam(**cam_config)

                # decode images
                prev_frame = self.decode_frame(value['prev_frame'])
                curr_frame = self.decode_frame(value['curr_frame'])

                # resize images
                prev_frame = cv2.resize(prev_frame, (cam.width, cam.height))
                curr_frame = cv2.resize(curr_frame, (cam.width, cam.height))

                cam.process_frame(prev_frame, curr_frame, self.ftp_config, self.database_config, self.mail_config)

                cv2.imshow("Current Frame", curr_frame)

                # Exit on pressing 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    cv2.destroyAllWindows()

def main():
    try:
        processor1 = FrameProcessor()
        processor1.consume_frame()
    except Exception as e:
        print(f"error: {e}")

if __name__ == "__main__":
    main()