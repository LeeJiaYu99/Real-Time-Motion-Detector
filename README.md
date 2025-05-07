## Real Time Motion Detector

This project demonstrates a real-time motion detection pipeline for any video feed or live stream that is supported by OpenCV (eg. .avi, .mov, .mp4...). There are two versions of the motion detector in this repository: [single_detector](https://github.com/LeeJiaYu99/Real-Time-Motion-Detector/tree/master/single_detector) and [multiple_detector](https://github.com/LeeJiaYu99/Real-Time-Motion-Detector/tree/master/multiple_detector).

- The [single_detector](https://github.com/LeeJiaYu99/Real-Time-Motion-Detector/tree/master/single_detector) version is a basic implementation designed to perform motion detection on a single video feed. It demonstrates the core logic of motion detection using frame differencing and image processing techniques in OpenCV.

- The [multiple_detector](https://github.com/LeeJiaYu99/Real-Time-Motion-Detector/tree/master/multiple_detector) version is a more scalable system built using **Kafka** as a middleware for distributing video frame data from multiple sources. It supports real-time motion analysis across several streams and is easily configurable for integrating additional video sources by updating the configuration file. Besides, this system can be containerized using the template in the provided **Dockerfile**, or orchestrated with **Kubernetes** using the manifest file. To run the system, simply place the appropriate program settings and video source details in the configuration file.

This system provides a foundation for building smart surveillance applications or other real-time video analytics solutions where motion detection is a key component.

### Motion Detection Technique
The logic used to build this motion detector is based on computing the absolute difference between a static background frame and the current frame which are preprocessed using a few **OpenCV** image processing techniques:
- Gaussian blur for noise reduction
- Binary thresholding and dilation to enhance motion regions
- Contour detection to localize moving objects.
Detected motion areas are then highlighted using bounding boxes for visualization.

![Demo](demo.gif)

[▶️ Full demo](https://www.youtube.com/shorts/adFPRxjSDdE)

### Scalable System Architecture
The [multiple_detector](https://github.com/LeeJiaYu99/Real-Time-Motion-Detector/tree/master/multiple_detector) version adopts a scalable, microservices-based architecture to support continuous real-time motion detection across multiple video streams. It consists of two components, each implemented as a microservice:

1. <mark>FrameCapturer</mark>
This service is responsible for extracting frames from video streams and publishing them to a Kafka topic. Frames are encoded in base64 and sent in pairs (previous and current frames) to enable motion comparison. Kafka acts as a message broker to ensure reliable distribution of frame data.

- FrameCapturer.py – Extracts frames and sends them to Kafka.
- config.json – Stores camera stream URLs and partition assignments.
- Dockerfile / docker-compose.yaml / manifest.yaml – Containerization and orchestration resources for deployment.

2. <mark>FrameMotionDetector</mark>
This service consumes messages from Kafka, performs motion detection on the received frame pairs, and executes appropriate actions such as saving frames, sending email alerts, or updating a database. The program is structured with object-oriented design.

- Cam.py – Defines the camera stream configuration and core frame processing logic.
- Region.py – Specifies the region of interest for motion analysis per camera.
- detector_scalable.py – Main application script that initializes and runs the detection system.
- config.json – Contains camera and detection region configurations.
- Dockerfile / manifest.yaml – Deployment configuration for Docker and Kubernetes. (When deployed on Kubernetes, the system can scale horizontally by increasing replicas to process messages from multiple Kafka partitions in parallel.)

<pre><code>
multiple_detector/
|-- FrameCapturer/
    |-- FrameCapturer.py
    |-- config.json
    |-- dockerfile
    |-- docker-compose.yaml
    |-- manifest.yaml
|-- FrameMotionDetector/
    |-- Cam.py
    |-- Region.py
    |-- config.json
    |-- detector_scalable.py
    |-- dockerfile
    |-- manifest.yaml
</code></pre>

### Deployment in Docker and Kubernetes
1. <mark>cd to FrameCapturer directory</mark> to build images for FrameCapturer apps of respective cameras initiated in config.json.
    <pre><code>
        docker compose build
    </code></pre>
        
    Optional: to push image to registry
    <pre><code>
        docker tag [image name] [registry image name]
        docker push [registry image name]
    </code></pre>

2. Create containers for the FrameCapturer images in Kubernetes.
    <pre><code>
        kubectl apply -f manifest.yaml
    </code></pre>

3. <mark>cd to FrameMotionDetector directory</mark> to build images for a single FrameMotionDetector app.
    <pre><code>
        docker build -t framemotiondetector:latest .
    </code></pre>
        
    Optional: to push image to registry
    <pre><code>
        docker tag framemotiondetector [registry image name]
        docker push [registry image name]
    </code></pre>

4. Create containers for the FrameMotionDetector image in Kubernetes.
    <pre><code>
        kubectl apply -f manifest.yaml
    </code></pre>

5. Scale the replicas for FrameMotionDetector if needed.
   <pre><code>
       kubectl scale --replicas=[number of replicas] deployment/framemotiondetector-app
    </code></pre>







