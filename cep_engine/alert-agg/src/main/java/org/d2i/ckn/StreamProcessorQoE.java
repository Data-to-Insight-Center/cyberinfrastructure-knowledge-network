package org.d2i.ckn;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.common.serialization.Serde;
import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.*;
import org.d2i.ckn.model.JsonSerde;
import org.d2i.ckn.model.qoe.AlertEvent;
import org.d2i.ckn.model.qoe.AverageAggregator;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

@Slf4j
public class StreamProcessorQoE {

    private static final ObjectMapper objectMapper = new ObjectMapper();  // Jackson's ObjectMapper instance
    private static String inputTopic;
    private static String outputTopic;
    private static String groupId;
    private static String bootstrapServers;
    private static String processorClientId;

    public static void main(String[] args) {
        // Load configuration properties from a file
        try (InputStream input = StreamProcessorQoE.class.getClassLoader().getResourceAsStream("config.properties")) {
            Properties config = new Properties();
            if (input == null) {
                log.error("The configuration file could not be found!");
                return;
            }
            config.load(input);

            // Assigning configuration properties to variables
            inputTopic = config.getProperty("stream.input.topic");
            outputTopic = config.getProperty("stream.output.topic");
            groupId = config.getProperty("stream.group.id");
            bootstrapServers = config.getProperty("stream.kafka.servers");
            processorClientId = config.getProperty("stream.kafka.clientId");
        } catch (IOException e) {
            // Throw runtime exception if configuration fails to load
            throw new RuntimeException(e);
        }

        // Set up stream processing properties
        Properties streamsProps = getProperties();

        // Build the stream processing topology
        StreamsBuilder builder = buildAlertEventStream();

        // Start the Kafka Streams application
        KafkaStreams kafkaStreams = new KafkaStreams(builder.build(), streamsProps);
        kafkaStreams.start();
    }

    // Builds the Kafka Streams topology for alert generation
    private static StreamsBuilder buildAlertEventStream() {
        StreamsBuilder streamsBuilder = new StreamsBuilder();
        Serde<AverageAggregator> averageAggregatorSerde = new JsonSerde<>(AverageAggregator.class);
        Serde<AlertEvent> alertEventSerde = new JsonSerde<>(AlertEvent.class);
        ObjectMapper objectMapper = new ObjectMapper();  // Ensure this is properly initialized

        KStream<String, AverageAggregator> inferenceEventKStream = streamsBuilder.stream(
                inputTopic,
                Consumed.with(Serdes.String(), averageAggregatorSerde)
        );

        inferenceEventKStream
                .filter((key, value) -> value.getAverage_req_accuracy() < 0.9)
                .mapValues(value -> new AlertEvent(
                        value.getServer_id(),
                        value.getService_id(),
                        value.getClient_id(),
                        "WARNING",
                        2,
                        "accuracy",
                        value.getAverage_req_accuracy(),
                        value.getTimestamp()
                ))
                .peek((key, value) -> {
                    try {
                        String json = objectMapper.writeValueAsString(value);
                        log.info(json);
                    } catch (Exception e) {
                        log.error("Failed to serialize AlertEvent", e);
                    }
                })
                .to(outputTopic, Produced.with(Serdes.String(), alertEventSerde));


        return streamsBuilder;
    }


    // Configuration properties for the Kafka Streams application
    private static Properties getProperties() {
        Properties configuration = new Properties();
        configuration.put(StreamsConfig.APPLICATION_ID_CONFIG, groupId);
        configuration.put(StreamsConfig.CLIENT_ID_CONFIG, processorClientId);
        configuration.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        configuration.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass().getName());
        configuration.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass().getName());
        configuration.setProperty(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, String.valueOf(1000));
        return configuration;
    }
}
