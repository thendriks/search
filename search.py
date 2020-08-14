#© 2020 By The Rector And Visitors Of The University Of Virginia

#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import requests,json, os,logging
from flask import Flask, render_template, request, redirect,jsonify
from requests.auth import HTTPBasicAuth

MONGO_HOST = os.environ.get('MONGO_HOST','mongo')
MONGO_PORT = os.environ.get('MONGO_PORT','27017')
MONGO_DB = os.environ.get('MONGO_DB','ors')
MONGO_USER = os.environ.get('MONGO_USER','mongoadmin')
MONGO_PASS= os.environ.get('MONGO_PASS','mongosecret')

MONGO_URI = "mongodb://{}:{}@{}:{}/{}?authSource=admin".format(MONGO_USER, MONGO_PASS, MONGO_HOST, MONGO_PORT, MONGO_DB)

STARDOG_USER = os.environ.get('STARDOG_USERNAME','username')
STARDOG_PASSWORD = os.environ.get('STARDOG_PASSWORD','password')
STARDOG_URL = os.environ.get('STARDOG_URL','http://stardog:5820/')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def search_mongo(query):

    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db['ids']

    ids = []
    cursor = collection.find({"$text": {"$search": query}})
    for document in cursor:
      ids.append(document['_id'])
    return query

def add_quotes(s):
    return "'" + s + "'"

def search_stardog(search):

    if search[0] != "'" and search[-1] != "'":
        search = add_quotes(search)

    query = "SELECT DISTINCT ?s ?score WHERE { ?s ?p ?l. (?l ?score) <tag:stardog:api:property:textMatch> $search.}"

    headers = {
      'Accept': 'application/sparql-results+json'
    }

    url = STARDOG_URL + 'ors/query?query=' + query + '&$search=' + search

    r = requests.get(url, auth=HTTPBasicAuth(STARDOG_USER, STARDOG_PASSWORD),headers = headers)
    result = r.json()

    if 'message' in result:
        return 'Search Failed'

    ids = []

    for bind in result['results']['bindings']:
        id = bind['s']['value']
        ids.append(id)

    return ids

@app.route('/<search>',methods = ['GET'])
def job_status(search):

    logger.info('Text Search for: %s', search)

    matching_ids = search_stardog(search)

    return jsonify({'matches':matching_ids})

if __name__ == "__main__":
    app.run(host='0.0.0.0')
