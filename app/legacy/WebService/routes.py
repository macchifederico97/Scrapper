from flask import Blueprint, jsonify, make_response
from WSPipelineRerun import pipeline_rerun
from WSPipelineRuntime import scrape_pipeline_last_run
from WSstatusScraper import scrape_pipeline_status
from WSUserStatus import scrape_user_list
from WSLogExtractor import log_extractor
from WSFullExtractor import full_extractor

api_blueprint = Blueprint("api", __name__)
headless = False    #True: page not showed (for prod purpose); False: page showed (for testing purpose)

# reruns the pipeline, Bifrost based
@api_blueprint.route("/rerun/<string:pipeline_name>/<string:bifrost_instance>", methods=["POST"])
def pipelineRerun(pipeline_name, bifrost_instance):
    data = pipeline_rerun(pipeline_name, bifrost_instance, headless)
    if data != "":
        return jsonify(data)
    else:
        return make_response(f"Pipeline {pipeline_name} not found", 404)

#returns the last pipeline runtime, Bifrost based
@api_blueprint.route("/runtime/<string:pipeline_name>/<string:bifrost_instance>", methods=["GET"])
def pipelineRuntime(pipeline_name, bifrost_instance):
    data = scrape_pipeline_last_run(pipeline_name, bifrost_instance, headless)
    if data != "":
        return jsonify(data)
    else:
        return make_response(f"Pipeline {pipeline_name} not found", 404)

#returns the last run status of all the pipelines in Bifrost, Bifrost based
@api_blueprint.route("/pipelineStatus/<string:filter>/<string:bifrost_instance>", methods=["GET"])
def pipelineStatus(filter, bifrost_instance):
    status = scrape_pipeline_status(bifrost_instance, filter, headless)
    return jsonify(status)


#returns the last log of the input pipeline, Bifrost based
@api_blueprint.route("/lastLog/<string:pipeline_name>/<string:bifrost_instance>", methods=["GET"])
def logExtractor(pipeline_name, bifrost_instance):
    output = log_extractor(pipeline_name, bifrost_instance, headless)
    if output != "":
        if output != "pipelineNotFound":
            return jsonify(output)
        else:
            return make_response(f"Pipeline {pipeline_name} not found", 404)    #Pipeline not found
    else:   #No log file handling
        return make_response(f"File not found for pipeline: {pipeline_name}", 404)      #Log file not found

#returns the last full run information of all the pipelines in Bifrost, Bifrost based
@api_blueprint.route("/pipelineFullExtract/<string:filter>/<string:bifrost_instance>", methods=["GET"])
def pipelineFullExtract(filter, bifrost_instance):
    fullStatus = full_extractor(bifrost_instance, filter, headless)
    return jsonify(fullStatus)


#returns information about all the users in the system, Visualfabriq based
@api_blueprint.route("/userStatus/<string:visualfabriq_instance>", methods=["GET"])
def userstatus(visualfabriq_instance):
    status = scrape_user_list(visualfabriq_instance, headless)
    return status

