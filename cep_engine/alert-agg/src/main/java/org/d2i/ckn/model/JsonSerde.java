package org.d2i.ckn.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import lombok.SneakyThrows;
import org.apache.kafka.common.serialization.Deserializer;
import org.apache.kafka.common.serialization.Serde;
import org.apache.kafka.common.serialization.Serializer;

public class JsonSerde<T> implements Serde<T> {
    public static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
    private final Class<T> type;
    private final Gson gson = new GsonBuilder().create();

    public JsonSerde(Class<T> type) {
        this.type = type;
    }

    @Override
    public Serializer<T> serializer() {
        return (key, data) -> serialize(data);
    }

    @Override
    public Deserializer<T> deserializer() {
        return (key, bytes) -> deserialize(bytes);
    }

    @SneakyThrows
    private byte[] serialize(T data) {
        return OBJECT_MAPPER.writeValueAsBytes(data);
    }

    @SneakyThrows
    private T deserialize(byte[] bytes) {
        return OBJECT_MAPPER.readValue(bytes, type);
    }
}
