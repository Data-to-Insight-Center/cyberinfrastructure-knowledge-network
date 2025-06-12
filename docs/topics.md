## Topic Names

A topic is a string used to identify and route messages between publishers and subscribers. The following topics are used by CKN daemons and recognized by CKN as subscriber. 

| Topic Name                   | System used by Publisher | Publisher          | Topic Purpose                                                                                               |
|------------------------------|----------------|--------------------------|-------------------------------------------------------------------------------------------------------------|
| oracle-events                | Kafka          | oracle_ckn_daemon        | Inference data from the [camera-traps application](https://github.com/tapis-project/camera-traps)           |
| cameratraps-power-summary    | Kafka          | oracle_ckn_daemon        | Aggregated power summary from the [camera-traps application](https://github.com/tapis-project/camera-traps) |
| cameratraps-accuracy-alerts  | Kafka          | experiment-alerts        | Alerts for experiments with accuracy below threshold (ID, accuracy, model ID, meta)                         |
| deployment_info              | Kafka          | ckn_inference_daemon     | Per‑inference result & resource metrics                                                                     |
| start_deployment             | Kafka          | ckn_inference_daemon     | Marks start of a deployment run                                                                             |
| end_deployment               | Kafka          | ckn_inference_daemon     | Marks graceful or abnormal termination                                                                      |
| cameratrap/events            | MQTT           | ckn-mqtt-cameratraps     | Camera trap event data (detections, storage actions, etc.)                                        |
| cameratrap/images            | MQTT           | ckn-mqtt-cameratraps     | Image data captured by camera traps                                                               |
| cameratrap/power_summary     | MQTT           | ckn-mqtt-cameratraps     | Aggregated power usage summaries from camera trap plugins                                         |


## Event Types and Formats

### cameratraps-power-summary

| Field                                             | Description                                           | Example                     |
|---------------------------------------------------|-------------------------------------------------------|-----------------------------|
| experiment_id                                     | Identifier for the experiment                         | googlenet-iu-animal-classification |
| image_generating_plugin_cpu_power_consumption     | CPU power usage for the image-generating plugin       | 2.63                        |
| image_generating_plugin_gpu_power_consumption     | GPU power usage for the image-generating plugin       | 0.076                       |
| power_monitor_plugin_cpu_power_consumption        | CPU power usage for the power-monitor plugin          | 2.59                        |
| power_monitor_plugin_gpu_power_consumption        | GPU power usage for the power-monitor plugin          | 0.071                       |
| image_scoring_plugin_cpu_power_consumption        | CPU power usage for the image-scoring plugin          | 2.57                        |
| image_scoring_plugin_gpu_power_consumption        | GPU power usage for the image-scoring plugin          | 0.082                       |
| total_cpu_power_consumption                       | Total CPU power usage across all plugins              | 7.79                        |
| total_gpu_power_consumption                       | Total GPU power usage across all plugins              | 0.229                       |

### oracle-events

| Field                    | Description                                        | Example                                 |
|--------------------------|----------------------------------------------------|-----------------------------------------|
| UUID                     | Unique identifier for the image/event              | 67b83445-2622-50a3-be3b-f7030259576e   |
| image_count              | Sequence number of the image                       | 2                                       |
| image_name               | File path or name of the image                     | /example_images/baby-red-fox.jpg        |
| ground_truth             | Expected (actual) label for the image              | animal                                  |
| model_id                 | Model identifier used for inference                | 0                                       |
| image_receiving_timestamp| Timestamp when the image was received              | 2024-08-06T20:46:14.130079257+00:00     |
| image_scoring_timestamp  | Timestamp when inference (scoring) was completed   | 2024-08-06T20:34:47.430327              |
| image_store_delete_time  | Time the image data was removed from storage       | 2024-08-06T20:34:47.438858883+00:00     |
| image_decision           | Action taken on the image (e.g., Save / Deleted)   | Save                                    |
| label                    | Predicted label with the highest probability       | animal                                  |
| probability              | Highest confidence score corresponding to label    | 0.924                                   |
| flattened_scores         | JSON-stringified array of all label-probability pairs | [{"label":"animal","probability":0.924}]|
| device_id                | The device that generated the event                | iu-edge-server-cib                      |
| experiment_id            | Identifier for the experiment                      | googlenet-iu-animal-classification      |
| user_id                  | User or owner of the experiment                    | jstubbs                                 |


### deployment_info  

| Field          | Description                                   | Example                                 |
|----------------|-----------------------------------------------|-----------------------------------------|
| timestamp      | Time when the event was recorded              | 2025-01-29T13:40:11.649Z                |
| server_id      | Unique identifier of the server               | edge-server-01                          |
| model_id       | Identifier of the deployed model              | resnet152-model                         |
| deployment_id  | Unique deployment instance ID                 | 123e4567-e89b-12d3-a456-426614174001    |
| service_id     | Name of the deployed service                  | imagenet_image_classification           |
| device_id      | Identifier of the device running the service  | camera-trap-device                      |
| ground_truth   | Expected outcome for validation               | cat                                     |
| req_delay      | Required delay constraint for the inference   | 0.05                                    |
| req_acc        | Required accuracy constraint                  | 0.90                                    |
| prediction     | Output prediction result                      | dog                                     |
| compute_time   | Time taken to compute the prediction          | 1.605                                   |
| probability    | Confidence score of the prediction            | 0.92956                                 |
| accuracy       | Binary indicator (0 or 1) for correct pred.   | 1                                       |
| total_qoe      | Overall Quality of Experience score           | 0.431                                   |
| accuracy_qoe   | QoE score based on accuracy                   | 0.837                                   |
| delay_qoe      | QoE score based on delay                      | 0.025                                   |
| cpu_power      | CPU power consumption in watts                | 0.0                                     |
| gpu_power      | GPU power consumption in watts                | 0.0                                     |
| total_power    | Total system power consumption in watts       | 0.0                                     |


### start_deployment

| Field         | Description                          | Example                                 |
|---------------|--------------------------------------|-----------------------------------------|
| deployment_id | Unique ID of the deployment instance | 123e4567-e89b-12d3-a456-426614174001    |
| server_id     | Unique identifier of the server      | edge-server-01                          |
| service_id    | Name of the deployed service         | imagenet_image_classification           |
| device_id     | Identifier of the device initiating  | camera-trap-device                      |
| model_id      | Identifier of the model being deployed| resnet152-model                        |
| status        | Indicates the current state          | RUNNING                                 |
| start_time    | Timestamp of deployment initiation   | 2025-01-29T13:08:48.401Z                |

### end_deployment

| Field         | Description                                 | Example                                 |
|---------------|---------------------------------------------|-----------------------------------------|
| deployment_id | Unique ID of the deployment instance        | 123e4567-e89b-12d3-a456-426614174001    |
| status        | Indicates the deployment has stopped        | STOPPED                                 |
| end_time      | Timestamp of deployment termination         | 2025-01-29T13:20:10.100Z                |

---

## MQTT Topic Event Types and Formats

### cameratrap/events

#### DETECTION Event
| Field           | Description                                  | Example                                        |
|-----------------|----------------------------------------------|------------------------------------------------|
| camera_trap_id  | Unique identifier of the camera trap device  | MLEDGE_1                                       |
| timestamp       | Event timestamp (ms since epoch)             | 1717029000000                                  |
| image_id        | Unique image identifier                      | MLEDGE_1_4b5d738e-9c8a-5097-96e7-3c78a00e0f31  |
| event_type      | Event type (always "DETECTION")              | DETECTION                                      |
| uuid            | Image UUID                                   | 4b5d738e-9c8a-5097-96e7-3c78a00e0f31           |
| classification  | Classification results (list of dicts)       | [{"label":"animal","probability":0.941}]       |

#### STORING Event
| Field           | Description                                  | Example                                        |
|-----------------|----------------------------------------------|------------------------------------------------|
| camera_trap_id  | Unique identifier of the camera trap device  | MLEDGE_1                                       |
| timestamp       | Event timestamp (ms since epoch)             | 1717029001234                                  |
| image_id        | Unique image identifier                      | MLEDGE_1_804f22de-8a90-52af-8baf-cda2cd66385f  |
| event_type      | Event type (always "STORING")                | STORING                                        |
| uuid            | Image UUID                                   | 804f22de-8a90-52af-8baf-cda2cd66385f           |
| file_location   | Path to image file                           | /images/dog.png                                |
| action          | Storage action taken (e.g., Save/Delete)     | Save                                           |

### cameratrap/images

| Field           | Description                                  | Example                                        |
|-----------------|----------------------------------------------|------------------------------------------------|
| camera_trap_id  | Unique identifier of the camera trap device  | MLEDGE_1                                       |
| timestamp       | Event timestamp (seconds since epoch)        | 1717029000.123                                 |
| image_id        | Unique image identifier                      | MLEDGE_1_804f22de-8a90-52af-8baf-cda2cd66385f  |
| uuid            | Image UUID                                   | 804f22de-8a90-52af-8baf-cda2cd66385f           |
| event_type      | Source event type (e.g., STORING)            | STORING                                        |
| file_location   | Path to image file                           | /images/dog.png                                |
| action          | Storage action taken (e.g., Save/Delete)     | Save                                           |
| image_data      | Base64-encoded image string                  | (very long base64 string)                      |

*Other fields may be included, as all fields from the related event are merged in.*

### cameratrap/power_summary

| Field                        | Description                                | Example                                        |
|------------------------------|--------------------------------------------|------------------------------------------------|
| camera_trap_id               | Unique identifier of the camera trap device| MLEDGE_1                                       |
| timestamp                    | Event timestamp (ms since epoch)           | 1717029000000                                  |
| total_cpu_power_consumption  | Total CPU power usage across all plugins   | 7.79                                           |
| total_gpu_power_consumption  | Total GPU power usage across all plugins   | 0.229                                          |
| [plugin]_cpu_power_consumption | CPU power usage per plugin               | 2.63                                           |
| [plugin]_gpu_power_consumption | GPU power usage per plugin               | 0.076                                          |
| experiment_id                | Identifier for the experiment (if present) | googlenet-iu-animal-classification             |

*Each `[plugin]` is replaced by the actual plugin name (e.g., image_generating_plugin, power_monitor_plugin, image_scoring_plugin).*

---
