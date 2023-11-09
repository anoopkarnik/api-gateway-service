from flask import Blueprint, request, jsonify
import os

payload_controller = Blueprint("payload_controller",__name__)

@payload_controller.route("/",methods=["GET"])
def health_check():
	return jsonify({"status":"success"})

@payload_controller.route("/notion",methods=['GET','POST','PATCH'])
def notion_service():
	service_port = os.environ.get('NOTION_SERVICE_PORT')
	service_url = f"http://0.0.0.0:{service_port}"
	response = requests.request(
		method=request.method,
		url=service_url,
		headers=[key:value for key,value in request.headers if key!='Host'],
		data=request.get_data(),
		cookies=request.cookies,
		allow_redirects=False
	)
	return (response.content, response.status_code, response.headers.items())
