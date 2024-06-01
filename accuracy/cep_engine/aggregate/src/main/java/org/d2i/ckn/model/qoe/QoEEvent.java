package org.d2i.ckn.model.qoe;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.d2i.ckn.model.EdgeEvent;

import java.util.Date;

@Data
@NoArgsConstructor
@Builder
@AllArgsConstructor
public class QoEEvent implements EdgeEvent {
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
    @JsonFormat(shape = JsonFormat.Shape.STRING,
            pattern = "dd-MM-yyyy hh:mm:ss")
    private Date added_time;
}
