import json
import os
import requests
from message import get_mm_recommendation, generate_mm_message
from dotenv import load_dotenv
import os

load_dotenv()

system_type = False

try:
    # Checks if the system runs on Hassio
    ACCESS_TOKEN = os.environ['SUPERVISOR_TOKEN']
    system_type = True
except:
    # generate access token from HA to test it locally
    ACCESS_TOKEN = os.getenv("LOCAL_ACCESS_TOKEN")

os.getenv("ACCESS_TOKEN")
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}


def get_ingress_url():
    response = requests.get(
        "http://supervisor/addons/self/info", headers=headers)
    addon_info = json.loads(response.text)
    prefix = addon_info['data']['ingress_url']
    hostname = addon_info['data']['hostname']
    port = addon_info['data']['ingress_port']
    etapp_host = f'http://{hostname}:{port}'
    return etapp_host, prefix


context = ''
if system_type:
    HOME_ASSISTANT_URL = 'http://supervisor/core'
    HOST, INGRESS_PREFIX = get_ingress_url()

    with open('/data/options.json', 'r') as f:
        hassio_config = json.load(f)
        SSL = hassio_config['ssl']
else:
    HOME_ASSISTANT_URL = "http://192.168.1.127:8123"
    INGRESS_PREFIX = '/'
    HOST = "http://192.168.1.121:5000"  # Local network flask app url


# ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NmFhN2I4OGE2YzU0N2IzOTM3ZmZlMTk4NmExMDI0NCIsImlhdCI6MTc0MTIwNjY1MywiZXhwIjoyMDU2NTY2NjUzfQ.AZF-ewRaXszWS81cwuTlGTf2feVCRrYjyZN_x3aBC24"

# node1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmYTk1YTk3MDQ4YjA0NzZhYTRkZjg5MWQ0ZDI3NjExMiIsImlhdCI6MTc0MTA4NzYyOCwiZXhwIjoyMDU2NDQ3NjI4fQ.tz1Re2LPjDjpfGRgcxlPtSQHJ6xq2ahFVIqAZWIFBFM"
# node2= "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NmFhN2I4OGE2YzU0N2IzOTM3ZmZlMTk4NmExMDI0NCIsImlhdCI6MTc0MTIwNjY1MywiZXhwIjoyMDU2NTY2NjUzfQ.AZF-ewRaXszWS81cwuTlGTf2feVCRrYjyZN_x3aBC24"

# INGRESS_PREFIX = get_ingress_url()

print(f"The host is: {HOST}, prefix is: {INGRESS_PREFIX}")


def get_entities():
    service_extension = '/api/states'
    response = requests.get(
        HOME_ASSISTANT_URL+service_extension, headers=headers)
    states = json.loads(response.text)
    switches = []
    lights = []
    persons = []
    sensors = []
    for entity in states:
        entity_id = entity['entity_id']
        if 'switch' in entity_id:
            switches.append(entity_id)
        elif 'light' in entity_id:
            lights.append(entity_id)
        elif 'person' in entity_id:
            persons.append(entity_id)
        elif 'sensor' in entity_id:
            sensors.append(entity_id)

    notify = []
    service_extension = '/api/services'
    response = requests.get(
        HOME_ASSISTANT_URL+service_extension, headers=headers)
    services = json.loads(response.text)
    for service in services:
        if service['domain'] == "notify":
            for key, cur_service in service['services'].items():
                if 'mobile_app_' in key:
                    notify.append(key)
    return notify, persons, switches, lights, sensors


def get_sersor_data(entity_name):
    url = f"{HOME_ASSISTANT_URL}/api/states/sensor.{entity_name}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(data)
        return float(data["state"])
    else:
        return None


def trigger_relay(command):  # command = "relay_on" or "relay_off"
    service_extension = "/api/services/shell_command/" + command
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(
        HOME_ASSISTANT_URL+service_extension, headers=headers)

    # print(response.ok)
    return response.ok


# trigger_relay('relay_on')


def send_notification(recommendation):
    """ Sends push notification to Home Assistant """
    service_extension = f"/api/services/notify/{recommendation.user.device}"
    print(service_extension)

    payload = {
        "title": f"Recommendation for {recommendation.automation.title} Automation",
        "message": recommendation.message,
        "data": {
            "actions": [
                {"action": f"ACCEPT_{recommendation.id}", "title": "Accept"},
                {"action": f"REJECT_{recommendation.id}", "title": "Reject"}
            ]
        }
    }
    response = requests.post(
        HOME_ASSISTANT_URL+service_extension, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"✅ Notification sent for recommendation {recommendation.id}")
    else:
        print(f"❌ Failed to send notification: {response.text}")


def add_ha_automation():
    """Adds the automation to Home Assistant via REST API"""
    if system_type:
        response_id = '04002025'  # for HA
    else:
        response_id = '04002026'  # for local testing
    service_extension = '/api/config/automation/config/'
    try:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        automation_data = {
            "id": response_id,
            "alias": "E-Twafeer Action Handler",
            "description": "Handles users action for recommendation and sends the response to the flask app.",
            "trigger": [
                {"platform": "event", "event_type": "mobile_app_notification_action"}
            ],
            "condition": [
                {
                    "condition": "template",
                    "value_template": "{{ trigger.event.data.action.startswith('ACCEPT_') or trigger.event.data.action.startswith('REJECT_') }}"
                }
            ],
            "action": [
                {
                    "service": "rest_command.send_recommendation_response",
                    "data": {
                        "host": f'{HOST}/recommendations/action',
                        "recommendation_id": "{{ trigger.event.data.action.split('_')[1] | int }}",
                        "action_taken": "{{ 'accepted' if trigger.event.data.action.startswith('ACCEPT_') else 'rejected' }}"
                    }
                }
            ],
            "mode": "single",
        }

        response = requests.get(
            HOME_ASSISTANT_URL+service_extension+response_id, headers=headers)
        if response.status_code == 404:
            response = requests.post(HOME_ASSISTANT_URL+service_extension+response_id,
                                     data=json.dumps(automation_data), headers=headers)

        if response.status_code == 201:
            print({"message": "Automation added successfully"})
        else:
            print({f"error: {response.text}, reponse_code : {response.status_code}"})

    except Exception as e:
        print({"error": str(e)})
