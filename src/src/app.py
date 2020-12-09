import os, re, requests
from sys import exit
from flask import Flask, request, Response
###############################################################################
#
# Project: Gitlab Issue Log Parser
# Author: James Anderton
# Date 12/08/2020
# Purpose: This is a mediator script that will receive a webhook sent from a
#   GitLab Issue being created. It will parse the json payload, looking for
#   the object_attributes[description] field. In this field it will trigger on
#   KEYWORD:Value pairs and separate them for use in a POST request. Finally
#   It will print out the equivalent Curl request for debugging use.
# CAVEAT: May need to parse json payload to lowercase False and switch None to
#   null
#
#############################################
app = Flask(__name__)
if not os.getenv("VAULT_TOKEN") or not os.getenv("GITLAB_TOKEN"):
    exit("VAULT_TOKEN and GITLAB_TOKEN environment variables are required.")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
BRANCH = os.getenv("BRANCH", default="master")
PORT = os.getenv("APP_PORT", default="3000")

# main route handler
@app.route("/", methods=["POST"])
def respond():
    data = request.get_json()
    # Pull fields from the webhook's json payload
    desc = data["object_attributes"]["description"]
    project_id = data["object_attributes"]["project_id"]
    # Parse the description field for templated key:value pairs
    data = parse_description(desc)
    # DEBUGGING:
    # print(data)
    customer = {}
    for item in data:
        if item:
            k, v = item[0].split(":")
            customer[k] = v
            # DEBUGGING
            # print(v)
    NAMESLUG = customer["NAMESLUG"]
    TEST_TEAM = customer["TEST_TEAM"]
    PROD_TEAM = customer["PROD_TEAM"]
    NAMESPACE = customer["NAMESPACE"]
    # # set up the payload to post to the CI/CD Pipeline as variables
    data = {"token": "token", "ref": "branch", "variables[MR_ID]": "VALUE"}
    # format data for for sending programmatically as a request via python
    req_payload = {
        "variables[NAMESLUG]": NAMESLUG,
        "variables[TEST_TEAM]": TEST_TEAM,
        "variables[PROD_TEAM]": PROD_TEAM,
        "variables[NAMESPACE]": NAMESPACE,
        "token": GITLAB_TOKEN,
        "ref": BRANCH,
        "variables[VAULT_TOKEN]": VAULT_TOKEN,
    }
    # format data for sending via CLI as a curl so we can print out for the user what we are doing
    curl_payload = (
        f"--form 'variables[NAMESLUG]'={NAMESLUG}"
        + f" --form 'variables[TEST_TEAM]'={TEST_TEAM}"
        + f" --form 'variables[PROD_TEAM]'={PROD_TEAM}"
        + f" --form 'variables[NAMESPACE]'={NAMESPACE}"
        + f" --form 'token'={GITLAB_TOKEN}"
        + f" --form 'ref'={BRANCH}"
        + f" --form 'variables[VAULT_TOKEN]'={VAULT_TOKEN}"
    )
    # Send a POST request to the already set up gitlab pipeline trigger
    req = requests.post(
        f"https://gitlab.com/api/v4/projects/{project_id}/trigger/pipeline?",
        req_payload,
    )
    # Print out the equivalent curl request for the user
    print(
        f"curl -X POST {curl_payload} https://gitlab.com/api/v4/projects/{project_id}/trigger/pipeline"
    )
    # Send the http response code as a result
    return Response(status=(req.status_code))
###### Func parse_description
###### REQUIRES: a string containing the description from the webhook payload
def parse_description(description):
    customer = []
    # parse thru the lines in the description field and split on keywords
    # then append them in K:V pairs to a list
    for line in description.split("\n"):
        if line:
            keywords = ["NAMESLUG", "TEST_TEAM", "PROD_TEAM", "NAMESPACE"]
            any_keyword = "|".join(map(re.escape, keywords))
            regex = "(" + any_keyword + "):(.+?)(?=(?:" + any_keyword + "):|$)"
            customer.append([m.string for m in re.finditer(regex, line)])
    return customer
# Start up our app on port 3000
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
