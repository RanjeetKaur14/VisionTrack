from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'face-events',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest'
)

print("Waiting...")

for message in consumer:
    print(message.value)