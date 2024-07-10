# CKN Camera-traps 

This repository contains the components and the setup to run CKN for TAPIS Camera Traps application.   

Oracle CKN Daemon:
- Daemon to read, process and send the camera-traps-oracle events. 
- Only the events that are fully processed (by the image_scoring_plugin) are extracted. 
- Dockerfile and Docker-compose files for ease of deployment of the daemon.

Dashboard:
- CKN Analytics dashboard for camera-traps

CKN Broker:
- Kafka broker and connector setup 
- Knowledge graph sinks for camera-traps events

CKN KG:
- Knowledge graph docker compose file





### Stream processors are available at:
[CKN Stream processors repository](https://github.com/Data-to-Insight-Center/ckn-stream-processors)