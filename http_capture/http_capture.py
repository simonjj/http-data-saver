from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
import json
import os
from sys import exit

# allow for different .env files
env = os.getenv('ENV', None)

if env:
    load_dotenv(".env.%s" % env)
else:
    load_dotenv(".env")

servicebus_client = None
namespace = os.getenv('SERVICE_BUS_NAMESPACE_CONNECTION_STRING', None)
queue = os.getenv('SERVICE_BUS_QUEUE_NAME', None)
if not namespace or not queue:
    raise Exception("SERVICE_BUS_NAMESPACE_CONNECTION_STRING and SERVICE_BUS_QUEUE_NAME must be set in .env file")    
else:
    print("Service bus namespace: ", namespace)
    print("Service bus queue: ", queue)

#class Item(BaseModel):
#    data: dict

@asynccontextmanager
async def service_bus_connection(app: FastAPI):
    global servicebus_client
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=namespace)
    print("Service bus client created")
    yield
    # Clean up the ML models and release the resources
    servicebus_client.close()
    print("Service bus client closed")
    

print("Starting FastAPI app")
app = FastAPI(lifespan=service_bus_connection)



@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def root(path: str, request: Request):
    body = await request.body()
    headers = dict(request.headers)
    method = request.method
    message = {
        "path": path,
        "body": body.decode(),
        "headers": headers,
        "method": method
    }
    asyncio.create_task(send_message_to_service_bus(json.dumps(message)))
    return Response(content=json.dumps({"message": "Message sent to queue"}), status_code=200)


async def send_message_to_service_bus(message):
    global servicebus_client
    async with servicebus_client:
        sender = servicebus_client.get_queue_sender(queue_name=queue)
        async with sender:
            message = ServiceBusMessage(message)
            await sender.send_messages(message)