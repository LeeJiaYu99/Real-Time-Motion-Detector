from shapely.geometry import Polygon
import logging
import requests

class Region:
    def __init__(self, name, region, cam_id):
        self.name = name
        self.cam_id= cam_id
        self.region = Polygon(region)
        self.trigger = False

        # Configure logging
        logging.basicConfig(
            filename='kafka_log.txt',
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.log = logging.getLogger(self.__class__.__name__)

    def get_region_info(self):
        """
        Returms a dictionary with the region information.
        """
        return {
            "name": self.name,
            "cam_id": self.cam_id,
            "region": self.region,
            "trigger": self.trigger
        }
    
    def motion_trigger(self, bbox):
        if self.region.intersects(bbox):
            self.trigger = True
            # self.send_trigger_update()
        else:
            self.trigger = False
        
        return self.trigger

    # # Yet to develop for frontend
    # def send_trigger_update(self):
    #     url = 'http://127.0.0.1:16/api/update_motion/'
    #     data = {
    #         "region": self.name,
    #         "cam_id": self.cam_id
    #     }
    #     response = requests.post(url, json=data)


        
