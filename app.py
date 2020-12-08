import json, os, re, requests

from flask import Flask, request, Response
app = Flask(__name__)

if os.getenv('VAULT_TOKEN'):
    VAULT_TOKEN = os.getenv('VAULT_TOKEN')

if os.getenv('GITLAB_TOKEN'):
    GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')

BRANCH = os.getenv('BRANCH')

# main route handler
@app.route('/', methods=['POST'])
def respond():
    data = request.get_json()

    # Pull fields from the webhook's json payload
    desc = data['object_attributes']['description']
    project_id = data['object_attributes']['project_id']
    
    # Parse the description field for templated key:value pairs
    data = parse_description(desc)
    print(data)
    customer = {}
    for item in data:
      if item:
        k,v = item[0].split(":")
        customer[k]=v
        print(v)

    NAMESLUG = customer['NAMESLUG']
    TEST_TEAM = customer['TEST_TEAM']
    PROD_TEAM = customer['PROD_TEAM']
    NAMESPACE = customer['NAMESPACE']

    # # set up the payload to post to the CI/CD Pipeline as variables
    data = {'token': 'token', 'ref': 'branch', 'variables[MR_ID]': 'VALUE'}
    req_payload = {'variables[NAMESLUG]': NAMESLUG, 'variables[TEST_TEAM]': TEST_TEAM, 'variables[PROD_TEAM]': PROD_TEAM, 'variables[NAMESPACE]': NAMESPACE, 'token': GITLAB_TOKEN, 'ref': BRANCH, 'variables[VAULT_TOKEN]': VAULT_TOKEN}

    curl_payload = "--form 'variables[NAMESLUG]'=" + str(NAMESLUG) + \
        " --form 'variables[TEST_TEAM]'=" + str(TEST_TEAM) + \
        " --form 'variables[PROD_TEAM]'=" + str(PROD_TEAM) + \
        " --form 'variables[NAMESPACE]'=" + str(NAMESPACE) + \
        " --form token='" + str(GITLAB_TOKEN) + \
        "' --form ref='" + str(BRANCH) + \
        "' --form 'variables[VAULT_TOKEN]'=" + str(VAULT_TOKEN)
     
    req = requests.post('https://gitlab.com/api/v4/projects/' + str(project_id) + '/trigger/pipeline?', req_payload)

    print('curl -X POST ' + str(curl_payload) + ' https://gitlab.com/api/v4/projects/' + str(project_id) + '/trigger/pipeline')
    
    return Response(status=(req.status_code))




def parse_description(description):
    customer = []
    for line in description.split("\n"):
        if line:     
            keywords = ['NAMESLUG', 'TEST_TEAM', 'PROD_TEAM', 'NAMESPACE']
            any_keyword = '|'.join(map(re.escape, keywords))
            regex = "(" + any_keyword + "):(.+?)(?=(?:" + any_keyword + "):|$)"
            customer.append([m.string for m in re.finditer(regex, line)])

    return customer

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=3000)
