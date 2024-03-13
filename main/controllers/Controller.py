from flask import Blueprint, request, jsonify, Response, stream_with_context
import os
import logging
import requests
import threading
from flask_cors import cross_origin

logger = logging.getLogger(__name__)

payload_controller = Blueprint("payload_controller",__name__)

def async_service_call(method, service_url, headers, data, cookies):
    try:
        response = requests.request(
            method=method,
            url=service_url,
            headers=headers,
            data=data,
            cookies=cookies,
            allow_redirects=False
        )
        logger.info(f"Response from {service_url}: {response.status_code}")
    except Exception as e:
        logger.error(f"Error in async call to {service_url}: {e}")

def stream_proxy_response(req_stream):
    def generate():
        for chunk in req_stream.iter_content(chunk_size=4096):
            yield chunk
    return Response(stream_with_context(generate()), content_type=req_stream.headers['Content-Type'])


@payload_controller.route("/",methods=["GET"])
def health_check():
	return jsonify({"status":"success"})

@payload_controller.route("/notion_stream/<path:subpath>", methods=['POST', 'GET', 'PATCH'])
@cross_origin()
def notion_stream_service(subpath):
    notion_service_network_name = os.environ.get('NOTION_SERVICE_NETWORK_NAME')
    notion_service_network_port = os.environ.get('NOTION_SERVICE_NETWORK_PORT')
    service_url = f"http://{notion_service_network_name}:{notion_service_network_port}/{subpath}"
    logger.info(f'Redirecting request to {service_url}')
    req = requests.post(service_url,data=request.data,headers=request.headers, stream=True)
    return stream_proxy_response(req)

@payload_controller.route("/notion/<path:subpath>", methods=['POST', 'GET', 'PATCH'])
@cross_origin()
def notion_service(subpath):
    notion_service_network_name = os.environ.get('NOTION_SERVICE_NETWORK_NAME')
    notion_service_network_port = os.environ.get('NOTION_SERVICE_NETWORK_PORT')
    service_url = f"http://{notion_service_network_name}:{notion_service_network_port}/{subpath}"
    logger.info(f'Redirecting request to {service_url}')
    if request.json.get('call_type','sync') == 'async':
    # Spawn a new thread for the service call
        threading.Thread(target=async_service_call, args=(
            request.method,
            service_url,
            {key: value for key, value in request.headers if key != 'Host'},
            request.get_data(),
            request.cookies
        )).start()

        return jsonify({"message": "Request is being processed"}), 202
    else:
        response = requests.request(
             method=request.method,
                url=service_url,
                headers={key:value for key,value in request.headers if key!='Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False
                )
        # print(response.content)
        return (response.content, response.status_code, response.headers.items())

@payload_controller.route("/chatgpt/<path:subpath>", methods=['POST', 'GET', 'PATCH'])
@cross_origin()
def chatgpt_service(subpath):
    chatgpt_service_network_name = os.environ.get('CHATGPT_SERVICE_NETWORK_NAME')
    chatgpt_service_network_port = os.environ.get('CHATGPT_SERVICE_NETWORK_PORT')
    service_url = f"http://{chatgpt_service_network_name}:{chatgpt_service_network_port}/{subpath}"
    logger.info(f'Redirecting request to {service_url}')

    if request.json.get('call_type','sync') == 'async':
    # Spawn a new thread for the service call
        threading.Thread(target=async_service_call, args=(
            request.method,
            service_url,
            {key: value for key, value in request.headers if key != 'Host'},
            request.get_data(),
            request.cookies
        )).start()

        return jsonify({"message": "Request is being processed"}), 202
    else:
        response = requests.request(
             method=request.method,
                url=service_url,
                headers={key:value for key,value in request.headers if key!='Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False
                )
        return (response.content, response.status_code, response.headers.items())
    
SERVICE_MAPPINGS = {'studio': 'supabase-studio','kong': 'supabase-kong','auth': 'supabase-auth','rest': 'supabase-rest',
    'realtime': 'realtime-dev.supabase-realtime','storage': 'supabase-storage','imgproxy': 'supabase-imgproxy',
    'meta': 'supabase-meta','functions': 'supabase-edge-functions','analytics': 'supabase-analytics','db': 'supabase-db',
    'vector': 'supabase-vector',
    # Add other services here if necessary
}
PORT_MAPPINGS = {'studio': '8005','kong': '8005','auth': '9999','rest': '3000',
    'realtime': '4000','storage': '5000','imgproxy': '5001',
    'meta': '8080','analytics': '4000','db': '5432',
    # Add other services here if necessary
}
    
@payload_controller.route("/<path:service_name>/<path:subpath>", methods=['POST', 'GET', 'PATCH','DELETE'])
@cross_origin()
def supabase_service(service_name,subpath):
    supabase_service_network_name = SERVICE_MAPPINGS.get(service_name)
    supabase_service_network_port = PORT_MAPPINGS.get(service_name)
    service_url = f"http://{supabase_service_network_name}:{supabase_service_network_port}/{subpath}"
    logger.info(f'Redirecting request to {service_url}')
    response = requests.request(
            method=request.method,
            url=service_url,
            headers={key:value for key,value in request.headers if key!='Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True
            )
    return Response(stream_with_context(response.iter_content()), content_type=response.headers['Content-Type'], status=response.status_code)
