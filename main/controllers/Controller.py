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
        return (response.content, response.status_code, response.headers.items())

@payload_controller.route("/chatgpt/<path:subpath>", methods=['POST', 'GET', 'PATCH'])
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
