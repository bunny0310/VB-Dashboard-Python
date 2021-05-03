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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime 
matplotlib.use('Agg')

app = Flask(__name__)
CORS(app) 
client = MongoClient('mongodb+srv://ikhurana:root@cluster0.gc8z6.mongodb.net/db?retryWrites=true&w=majority', ssl_cert_reqs=ssl.CERT_NONE)
db = client['db']
users = db.users
words = db.words


# method to convert a word to a list of tags
def TagsFromWords(words):
    tags = []
    for word in words:
        tags.extend(word['tags'])
    
    tags = list(filter(None, tags))
    return tags

#mask for book cloud
# bookMask = np.array(Image.open("book.png"))

@app.route('/tags', methods = ['POST'])
def tags():
    data = request.get_json()
    if 'username' not in data:
        return jsonify({"message": "incorrectly formated data"})
    
    username = data['username'];
    user = users.find_one({'username': username})
    if user is None:
        return jsonify({"message": "user not found"})
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

    return make_response({
        'status': True,
        'code': 200,
        'imageData': imgString
    })

@app.route('/monthly-tags-info', methods = ['POST'])
def infoTags():
    data = request.get_json()
    if 'username' not in data:
        return jsonify({"message": "incorrectly formated data"})   
    username = data['username']

    user = users.find_one({'username': username});
    if user is None:
        return jsonify({"message": "user not found"}) 
    
    listWords = words.find({'user': user['_id']})
    tags = TagsFromWords(listWords);
    freqs = Counter(tags)
    vals = list(freqs.values())
    vals.sort()
    vals.reverse()
    freqArr = np.array(vals[0:5])
    labels = list()
    sortedFreqs = sorted(freqs.items(), key=lambda item: item[1])
    sortedFreqs.reverse()
    for k, v in sortedFreqs[0:5]:
        labels.append(k)
    
    plt.clf()
    plt.pie(freqArr, labels=labels, shadow=True, explode=[0.01, 0.01, 0.01, 0.01, 0.01])
    plt.legend(title='Top 5 Tags:')
    plt.savefig(username + '-pie.png')
    with open(username + '-pie.png', "rb") as img_file:
        imgString = base64.b64encode(img_file.read()).decode('utf-8')
        if os.path.exists(username + '-pie.png'):
            os.remove(username + '-pie.png')
            print('file removed')
        return make_response(jsonify({
            'code': 200,
            'status': True,
            'imageData': imgString
        }))

@app.route('/acc-info', methods = ['POST'])    
def info():
    data = request.get_json()

    if 'username' not in data:
        return jsonify({"message": "incorrectly formated data"})   
    username = data['username']

    user = users.find_one({'username': username});
    if user is None:
        return jsonify({"message": "user not found"}) 
    
    recent = True
    if 'recent' not in data:
        print('regular')
        recent = False
    
    uid = user['_id'];
    listWords = words.find({'user': user['_id']}).sort('createdAt', -1)
    today = datetime.datetime.today()
    d2 = datetime.datetime(today.year, today.month, 1)
    recentWords = []
    if recent:
        for word in listWords:
            d1 = word['createdAt']
            if d1 >= d2:
                recentWords.append(word)
    
    if not recent:
        recentWords = list(listWords)

    print(len(recentWords))
    ans = {}
    types = {}

    ans['wordcount'] = len(list(recentWords))
    tags = TagsFromWords(recentWords);
    freqs = Counter(tags)
    keys = list(freqs.keys())
    ans['uniqueTags'] = len(list(keys))

    for word in recentWords:
        for type in word['types']:
            type = type.title()
            if type in types:
                types[type] = types[type] + 1
            else:
                types[type] = 1
    
    vals = list(types.values())
    labels = list(types.keys())
    plt.clf()
    plt.pie(vals, labels=labels, shadow=True)
    plt.legend(title='Breakdown by types of words:', bbox_to_anchor=(1, 0.83), loc="center right", fontsize=10, 
           bbox_transform=plt.gcf().transFigure)
    plt.savefig(username + '-types.png')
    with open(username + '-types.png', "rb") as img_file:
        typesImgStr = base64.b64encode(img_file.read()).decode('utf-8')
        # if os.path.exists(username + '-types.png'):
        #     os.remove(username + '-types.png')
        #     print('file removed')
        
        ans['types'] = typesImgStr
        return make_response(jsonify({
            'code': 200,
            'status': True,
            'wordCount': ans['wordcount'],
            'uniqueTags': ans['uniqueTags'],
            'imageData': ans['types']
        }))
