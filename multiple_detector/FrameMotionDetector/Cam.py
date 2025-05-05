import cv2
from Region import Region
sys.path.insert(0, r"..\motion_detector\utils")
from detector_utils import detect_motion
from datetime import datetime
from shapely.geometry import box

import sys
from ftplib import FTP
import io
import oracledb

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

class Cam:
    """
    A class to define camera configuration and motion detection function.
    """
    def __init__(self, cam_id, video_path, video_width, video_height, regions):
        self.cam_id = cam_id
        self.video_path = video_path
        self.width = video_width
        self.height = video_height
        self.regions = [Region(**region, cam_id=cam_id) for region in regions]

    def process_frame(self, prev_frame, curr_frame, ftp_config, database_config, mail_config):
        """
        Detect motion in between two frames
        """
        merged_boxes = detect_motion(prev_frame, curr_frame)

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        for (x, y, w, h) in merged_boxes:
            for region in self.regions:
                if region.region.motion_trigger(box(x, y, x+w, y+h)):
                    cv2.rectangle(curr_frame, (x, y), (x + w, y + h), (0, 255, 0), 2) 
                    _, img_encoded = cv2.imencode('.png', curr_frame)
                    # print("Motion detected")
                    self.save_result(timestamp, curr_frame, region.name, ftp_config, database_config)
                    self.email_triggering(img_encoded, region.name, mail_config)
            
    def upload_img_to_ftp(self, frame, timestamp, ftp_config) :
        # Encode the image to binary format
        _, buffer = cv2.imencode(' .jpg', frame)
        buffer_io = io.BytesIO(buffer.tobytes())

        try:
            ftp = FTP(ftp_config['ip'])
            ftp.login(user=ftp_config['user'], passwd=ftp_config['password'])
            # Change to the target directory (if specified)
            ftp_directory = ftp_config["dir"]
            if ftp_directory:
                ftp.cwd(ftp_directory)
            else:
                ftp.mkd(ftp_directory)
            ftp.storbinary(f"STOR {timestamp}.jpg, buffer_io")
            ftp.quit()

            return f"{ftp_directory}/{timestamp}.jpg"
        except Exception as e:
            print(f"Failed to upload image to FTP server: {e}")

    def save_result(self, timestamp, frame, region, ftp_config, database_config):
        image_path = self.upload_img_to_ftp(frame, timestamp, ftp_config)

        try:
            # Connect to Oracle database
            connection = oracledb.connect(
                user=database_config['user'],
                password=database_config['pasword'],
                sid=database_config['id'],
                host=database_config['host'],
                port=database_config['port']
                )
            cursor = connection.cursor()

            sql_insert = """
            INSERT INTO MOTION_TABLE (DATETIME, IMAGE_PATH, REGION)
            VALUES (to_char(to_date(:timestamp, 'YYYY_MM_DD HH24_MI_SS'), 'YYYY-MM-DD HH24:MI:SS'), :image_path, :region)
            """

            data ={
                "timestamp": timestamp,
                "image_path": image_path,
                "region": region
            }
            cursor.execute(sql_insert, data)
            connection.commit()

            cursor.close()
            connection.close()
        except Exception as e:
            print(f"Failed to save info: {e}")

    def email_triggering(self, img_encoded, region, mail_config):
        smtp_server = mail_config['server']
        smtp_port = mail_config['port']
        sender_email = mail_config['sender']
        sender_name = mail_config['sender_name']
        receiver_email = mail_config['receiver']
        subject = "Monitoring Admin"
        body = f"""
        <html>
            <body>
                <h2>{self.cam_id}</h2>
                <p>Dear sir/mdm,</p>
                <p>Motion detected at {region} by {self.cam_id}.</p>
                <img src="cid=image1" alt="Embedded Image">
            </body>
        </html>
        """

        # Create an in-memory binary stream for the image
        img_bytes = io.BytesIO(img_encoded.tobytes())

        # Create a MIMEMultipart email
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Attach the HTML body
        msg.attach(MIMEText(body, 'html'))

        # Attach the image
        img = MIMEImage(img_bytes.read(), _subtype='png', name='image.png')
        img.add_header('Content-ID', '<image1>')    # Matches the CID in the HTML body
        msg.attach(img)

        # Send the email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.set_debuglevel(1)    # Optional: enable debug output for troubleshooting
                server.send_message(msg)
            print("Email sent successfully!")
        except Exception as e:
            print("Failed to send email: {'e}")

