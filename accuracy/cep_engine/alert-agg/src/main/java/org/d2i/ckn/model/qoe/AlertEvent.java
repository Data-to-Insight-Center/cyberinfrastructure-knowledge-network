package org.d2i.ckn.model.qoe;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Getter;
import lombok.Setter;

public class AlertEvent {
    @Getter @Setter private String server_id;
    @Getter @Setter private String service_id;
    @Getter @Setter private String client_id;
    @Getter @Setter private String type;
    @Getter @Setter private Integer priority;
    @Getter @Setter private String metric;
    @Getter @Setter private float value;
    @Getter @Setter
//    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "dd-MM-yyyy hh:mm:ss")
    private long added_time;

    public AlertEvent(String serverId, String serviceId, String clientId, String type, Integer priority, String metric, float value, String addedTime) {
        this.server_id = serverId;
        this.service_id = serviceId;
        this.client_id = clientId;
        this.type = type;
        this.priority = priority;
        this.metric = metric;
        this.value = value;
        this.added_time = Long.parseLong(addedTime);
    }
}
