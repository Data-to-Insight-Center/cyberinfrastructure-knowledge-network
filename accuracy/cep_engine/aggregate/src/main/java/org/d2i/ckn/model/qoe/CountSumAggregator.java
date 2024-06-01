package org.d2i.ckn.model.qoe;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CountSumAggregator{
    private long count = 0;
    private float accuracy_total = 0;
    private float delay_total = 0;
    private float qoe_total_sum = 0;
    private float qoe_delay_total = 0;
    private float qoe_acc_total = 0;
    private float pred_acc_total = 0;
    private float compute_time_total = 0;
    private String client_id = "2";
    private String service_id = "2";
    private String server_id = "2";
    private String model = "2";

    public CountSumAggregator process(InferenceEvent inferenceEvent) {
        this.client_id = inferenceEvent.getClient_id();
        this.service_id = inferenceEvent.getService_id();
        this.server_id = inferenceEvent.getServer_id();
        this.model = inferenceEvent.getModel();
        this.count++;
        this.accuracy_total += inferenceEvent.getReq_acc();
        this.delay_total += inferenceEvent.getReq_delay();
        this.qoe_total_sum += inferenceEvent.getTotal_qoe();
        this.qoe_delay_total += inferenceEvent.getDelay_qoe();
        this.qoe_acc_total += inferenceEvent.getAccuracy_qoe();
        this.pred_acc_total += inferenceEvent.getPred_accuracy();
        this.compute_time_total += inferenceEvent.getCompute_time();
//        log.info(this.toString());
        return this;
    }
}
