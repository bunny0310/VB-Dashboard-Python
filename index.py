from flask import Flask
from pymongo import MongoClient
from flask import Flask, request, jsonify, make_response
import json
from flask_cors import CORS, cross_origin
import ssl
import numpy as np
from bson.objectid import ObjectId
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from collections import Counter
import base64, os

app = Flask(__name__)
CORS(app) 
client = MongoClient('mongodb+srv://ikhurana:ishaan123@cluster0.gc8z6.mongodb.net/db?retryWrites=true&w=majority', ssl_cert_reqs=ssl.CERT_NONE)
db = client['db']
users = db.users
words = db.words

# method to convert a word to a list of tags
def mapWordToTags(word):
    return word.tags

#mask for book cloud
# bookMask = np.array(Image.open("book.png"))

@app.route('/tags', methods = ['POST'])
def tags():
    data = request.get_json()
    if 'username' not in data:
        return jsonify({"message": "incorrectly formated data"})
    
    username = data['username'];
    user = users.find_one({'username': username})
    uid = user['_id'];
    words = globals()['words'].find({'user': uid})
    tags = []
    for word in words:
        tags.extend(word['tags'])
    
    tags = list(filter(None, tags))
    freqs=Counter(tags)
    wordcloud = WordCloud(max_font_size=50, background_color="white", contour_width=3, contour_color='firebrick', random_state=42).generate_from_frequencies(freqs)
    #save image
    wordcloud.to_file('cloud-' + username + '.png')

    im = Image.open('cloud-' + username + '.png')
    with open('cloud-' + username + '.png', "rb") as img_file:
        imgString = base64.b64encode(img_file.read()).decode('utf-8')
    
    if os.path.exists('cloud-' + username + '.png'):
        os.remove('cloud-' + username + '.png')
        print('file removed')

    return make_response({"msg": str(imgString)})