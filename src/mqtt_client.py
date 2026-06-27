import paho.mqtt.client as mqtt


def create_mqtt_client(
    client_id: str,
    broker: str = "localhost",
    port: int = 1883,
) -> mqtt.Client:
    client = mqtt.Client(client_id=client_id)
    client.connect(broker, port)
    return client
