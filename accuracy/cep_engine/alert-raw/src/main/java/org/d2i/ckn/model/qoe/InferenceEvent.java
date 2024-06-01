package org.d2i.ckn.model.qoe;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.*;
import org.d2i.ckn.model.EdgeEvent;

import java.util.Date;

@Data
@NoArgsConstructor
@Builder
@AllArgsConstructor
public class InferenceEvent implements EdgeEvent {
    private String server_id;
    private String service_id;
    private String client_id;
    private String prediction;
    private float compute_time;
    private float pred_accuracy;
    private float total_qoe;
    private float accuracy_qoe;
    private float delay_qoe;
    private float req_acc;
    private float req_delay;
    private String model;
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "dd-MM-yyyy hh:mm:ss")
    private Date added_time;

    // Lombok will generate these getters (and setters)
    public String getServer_id() {
        return server_id;
    }

    public String getService_id() {
        return service_id;
    }

    public String getClient_id() {
        return client_id;
    }

    public String getPrediction() {
        return prediction;
    }

    public float getCompute_time() {
        return compute_time;
    }

    public float getPred_accuracy() {
        return pred_accuracy;
    }

    public float getTotal_qoe() {
        return total_qoe;
    }

    public float getAccuracy_qoe() {
        return accuracy_qoe;
    }

    public float getDelay_qoe() {
        return delay_qoe;
    }

    public float getReq_acc() {
        return req_acc;
    }

    public float getReq_delay() {
        return req_delay;
    }

    public String getModel() {
        return model;
    }

    public Date getAdded_time() {
        return added_time;
    }
}

