import signal
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.servicebus.exceptions import ServiceBusConnectionError
import json
import os
import httpx

# allow for different .env files
env = os.getenv('ENV', None)

if env:
    load_dotenv(".env.%s" % env)
else:
    load_dotenv(".env")

servicebus_client = None
namespace = os.getenv('SERVICE_BUS_NAMESPACE_CONNECTION_STRING', None)
queue = os.getenv('SERVICE_BUS_QUEUE_NAME', None)
downstream_endpoint = os.getenv('DOWNSTREAM_ENDPOINT', None)
if not namespace or not queue:
    raise Exception("SERVICE_BUS_NAMESPACE_CONNECTION_STRING and SERVICE_BUS_QUEUE_NAME must be set in .env file")    
else:
    print("Service bus namespace: ", namespace)
    print("Service bus queue: ", queue)
    print("Downstream endpoint: ", downstream_endpoint)


@asynccontextmanager
async def service_bus_connection():
    global servicebus_client
    print("Creating service bus client")
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=namespace, logging_enable=True)
    print("Service bus client created")
    yield servicebus_client
    # Clean up the ML models and release the resources
    servicebus_client.close()
    print("Service bus client closed")


async def receive_message_from_service_bus():
    print("starting main loop....")
    global downstream_endpoint
    async with service_bus_connection() as servicebus_client:
        print("Creating message receiver...")
        receiver = servicebus_client.get_queue_receiver(queue_name=queue)
        while True:
            print("Waiting for messages...")
            messages = None
            try:
                messages = await receiver.receive_messages(max_message_count=5, max_wait_time=5)
            except ServiceBusConnectionError as e:
                print(f"Failed to receive messages from service bus: {e}")
                continue
            for message in messages:
                content = next(message.body)
                data = json.loads(content)
                path = data["path"]
                headers = data["headers"]
                method = data["method"]
                body = data["body"]
                print(f"Received message with path {path}, headers {headers}, method {method}, body {body[:200]}")
                url = f"{downstream_endpoint}/{path}"
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.request(method, url, headers=headers, data=body)
                        print(f"Sent request to {url}, received status code {response.status_code}")
                        await receiver.complete_message(message)
                except Exception as e:
                    print(f"Failed to send request to {url}, maybe the downstream endpoint is down? Message:\n {e}")
                


def shutdown(signal, loop):
    print(f"Received exit signal {signal.name}...")
    loop.stop()


if __name__ == "__main__":
    print("Starting service bus receiver...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )
    try:
        loop.run_until_complete(receive_message_from_service_bus())
    finally:
        loop.close()


print("doing something")