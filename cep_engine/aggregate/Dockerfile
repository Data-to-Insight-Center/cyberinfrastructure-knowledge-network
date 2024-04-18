FROM openjdk:11-jre-slim

EXPOSE 8080

ARG JAR_FILE=./target/ckn-streaming-1.0-SNAPSHOT-jar-with-dependencies.jar

ADD ${JAR_FILE} ckn-stream-processor.jar

ENTRYPOINT ["java","-jar","/ckn-stream-processor.jar"]