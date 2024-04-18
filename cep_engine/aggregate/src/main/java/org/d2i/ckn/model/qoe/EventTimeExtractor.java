package org.d2i.ckn.model.qoe;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.streams.processor.TimestampExtractor;

import java.util.Optional;

public class EventTimeExtractor implements TimestampExtractor {
    @Override
    public long extract(ConsumerRecord<Object, Object> consumerRecord, long partitionTime) {
        InferenceEvent inferenceEvent = (InferenceEvent) consumerRecord.value();
        return Optional.ofNullable(inferenceEvent.getAdded_time())
                .map(at -> at.toInstant().toEpochMilli())
                .orElse(partitionTime);
    }
}
