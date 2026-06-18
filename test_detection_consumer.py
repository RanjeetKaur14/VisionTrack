from kafka import KafkaConsumer

consumer = KafkaConsumer(
    "detection-events",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="latest"
)

print("Listening for detection events...")

for message in consumer:

    print(
        message.value.decode("utf-8")
    )