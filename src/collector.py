import signal
import sys
import time

import psutil

from src.mqtt_client import create_mqtt_client


def main() -> None:
    client = create_mqtt_client("collector-pc")
    client.loop_start()

    def cleanup(signum, frame):
        print("Encerrando...")
        client.loop_stop()
        client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)

    while True:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        client.publish("sistema/pc/cpu", f"{cpu:.0f}", qos=1)
        client.publish("sistema/pc/ram", f"{ram:.0f}", qos=1)
        print(f"CPU: {cpu:.0f}% | RAM: {ram:.0f}%")
        time.sleep(2)


if __name__ == "__main__":
    main()
