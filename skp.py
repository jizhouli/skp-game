# -*- coding: utf-8 -*-

import json

import redis
import pymysql

from lib.tencent_ocr import TencentOcr
from lib.tencent_face import get_beauty
from lib.tencent_object import get_object

from flask import Flask, jsonify, request
app = Flask(__name__)


#################### Conf ####################

DB_HOST = ''
DB_USER = ''
DB_PASSWORD = ''
DB_DATABASE = ''

REDIS_HOST = ''
REDIS_PORT = 6379
REDIS_PASSWORD = ''
REDIS_DATABASE = 0

#################### MySQL ####################

def mysql_query(sql):
    db = pymysql.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)
    cursor = db.cursor()
    cursor.execute(sql)
    data = cursor.fetchone()
    db.close()

    return data

def mysql_update(sql):
    db = pymysql.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE)
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
    except:
        db.rollback()
    db.close()

    return

def create_user(open_id):
    sql = 'insert into user_info (`open_id`) values("{}")'.format(open_id)
    mysql_update(sql)

def get_user_info(open_id):
    sql = 'select * from user_info where open_id="{}"'.format(open_id)
    data = mysql_query(sql)
    if not data:
        create_user(open_id)
        data = mysql_query(sql)
    
    user_info = dict()
    user_info['open_id'] = data[0]
    user_info['test1_score'] = data[1]
    user_info['test2_score'] = data[2]
    user_info['test3_score'] = data[3]
    user_info['test4_score'] = data[4]
    user_info['test5_score'] = data[5]
    user_info['try_num'] = data[6]
    user_info['img1'] = data[7]
    user_info['img2'] = data[8]
    user_info['img3'] = data[9]
    user_info['img4'] = data[10]
    user_info['img5'] = data[11]
    
    return user_info

#def get_try_num(open_id):
#    user_info = get_user_info(open_id)
#    return user_info['try_num']

#def add_try_num(open_id):
#    sql = 'update user_info SET try_num = try_num + 1 where open_id="{}";'.format(open_id)
#    mysql_update(sql)

#################### Redis ####################

def redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DATABASE, decode_responses=True)

def get_int(key):
    r = redis_client()
    v = r.get(key)
    if v is None:
        r.set(key, 0)
        v = r.get(key)
    return int(v)

def set_int(key, val):
    r = redis_client()
    r.set(key, val)

def get_str(key):
    r = redis_client()
    v = r.get(key)
    if v is None:
        return ''
    return v

def set_str(key, val):
    r = redis_client()
    r.set(key, val)

def get_try_num(open_id, action):
    key = '{}_{}_try'.format(open_id, action)
    return get_int(key)

def add_try_num(open_id, action):
    key = '{}_{}_try'.format(open_id, action)
    try_num = get_int(key)
    set_int(key, try_num+1)

def set_score(open_id, action, score):
    key = '{}_{}_score'.format(open_id, action)
    old_score = get_int(key)
    new_score = max(old_score, score)
    set_int(key, new_score)

def set_avatar(open_id, img_url):
    key = '{}_avatar'.format(open_id)
    set_str(key, img_url)

def is_lucky(open_id, idol_score):
    if not (idol_score > 0 and idol_score%5 == 0):
        return False
    
    # get lucky limit
    key_limit = 'luck_list_limit'
    limit = get_int(key_limit)
    if limit == 0:
        return False

    # get lucky ones
    key = 'luck_list'
    luck_list_str = get_str(key)
    if not luck_list_str:
        set_str(key, '[]')
        luck_list_str = get_str(key)
    luck_list = json.loads(luck_list_str)
    
    # already get gift
    if open_id in luck_list:
        return False
    
    # new lucky one
    luck_list.append(open_id)
    set_str(key, json.dumps(luck_list)) # update list
    set_int(key_limit, limit-1) # update list limit
    return True

def get_profile(open_id):
    # basic info
    profile = {
        'open_id': open_id,
        'avatar': get_str('{}_avatar'.format(open_id))
    }
    # score info
    all_scores = ['song_score', 'brain_score', 'exercise_score', 'reco_ocr_score', 'reco_object_score', 'reco_face_score']
    total = 0
    for type in all_scores:
        score = get_int('{}_{}'.format(open_id, type))
        profile[type] = score
        total += score
    # idol score info
    idol_score = int(total/len(all_scores)) if len(all_scores)>0 else 0
    profile['idol_score'] = idol_score
    # some lucky ones get gift
    profile['is_lucky'] = is_lucky(open_id, idol_score)
    
    return profile


#################### Game Basecode ####################

def calc_score(open_id, action, is_correct):
    try_num = get_try_num(open_id, action)
    if try_num >= 4:
        return True, 60

    if is_correct:
        score = 100 - try_num*10
    else:
        score = 0
    add_try_num(open_id, action)

    set_score(open_id, action, score)
    return is_correct, score

#################### Handler Response ####################

class Response(object):
    def __init__(self, open_id, correct, score):
        self.open_id = open_id
        self.correct = correct
        self.score = score
    
    def dict(self):
        return {
            'open_id': self.open_id,
            'correct': self.correct,
            'score': self.score
        }
    
    def json(self):
        return jsonify(self.dict())

#################### Route Handlers ####################

songs = dict()
songs['jiandanai'] = u'我想就这样牵着你的手不放开'

def text_similarity(t1, t2):
    bag = dict()
    total = 0
    for c in t1:
        total += 1
        if c not in bag:
            bag[c] = 1
        else:
            bag[c] += 1
    for c in t2:
        if c in bag and bag[c] > 0:
            bag[c] -= 1
    
    diff = 0
    for k in bag:
        diff += bag[k]

    if total == 0: return 0
    else: return float(total-diff)/float(total)

def song_handler(open_id, req):  

    resp = Response(open_id, False, 0)

    # game rule
    name = req.get('name', 'jiandanai')
    answer = req.get('answer', '')
    sim = text_similarity(songs[name], answer)
    if sim > 0.8: correct = True
    else: correct = False

    # judgement
    correct, score = calc_score(open_id, 'song', correct)

    resp.correct = correct
    resp.score = score
    return resp.json(), 200

def brain_handler(open_id, req):  

    resp = Response(open_id, False, 0)

    # game rule
    answer = req.get('answer', '')
    if answer in ('B', 'b'): correct = True
    else: correct = False

    # judgement
    correct, score = calc_score(open_id, 'brain', correct)

    resp.correct = correct
    resp.score = score
    return resp.json(), 200

def exercise_handler(open_id, req):

    resp = Response(open_id, False, 0)

    # game rule
    answer = req.get('answer', 0)
    if answer >= 888: correct = True
    else: correct = False

    # judgement
    correct, score = calc_score(open_id, 'exercise', correct)

    resp.correct = correct
    resp.score = score
    return resp.json(), 200

def reco_object_handler(open_id, req):
    
    resp = Response(open_id, False, 0)

    img_url = req.get('img_url', '')
    text = req.get('text', '')
    import random
    correct = True if random.randint(0,9) < 6 else False

    obj_name = get_object(img_url)
    if text in obj_name: correct = True
    else: correct = False

    # judgement
    correct, score = calc_score(open_id, 'reco_object', correct)

    resp.correct = correct
    resp.score = score
    return resp.json(), 200

def reco_ocr_handler(open_id, req):
    
    resp = Response(open_id, False, 0)

    img_url = req.get('img_url', '')
    text = req.get('text', '')
    
    ocr = TencentOcr()
    reco_text = ocr.get_image_text(img_url)
    correct = True if text in reco_text else False

    # judgement
    correct, score = calc_score(open_id, 'reco_ocr', correct)

    resp.correct = correct
    resp.score = score
    return resp.json(), 200

def reco_face_handler(open_id, req):

    resp = Response(open_id, False, 0)

    img_url = req.get('img_url', '')

    score = get_beauty(img_url)
    set_score(open_id, 'reco_face', score)
    set_avatar(open_id, img_url) # save avatar

    resp.correct = True # absolutely always be True
    resp.score = score
    return resp.json(), 200

def profile_handler(open_id, req):
    return jsonify(get_profile(open_id)), 200


#################### Request Dispatcher ####################

@app.route("/", methods=['POST'])
def root_route():
    req = request.json

    # check open_id
    open_id = req.get('open_id', '')
    if not open_id:
        return jsonify({'error': 'open_id is a required parameter'}), 404
    
    # check action
    action = req.get('action', '')
    if not action:
        return jsonify({'error': 'action is a required parameter'}), 404
    
    # dispatch requests
    if action == 'song':
        return song_handler(open_id, req)
    elif action == 'brain':
        return brain_handler(open_id, req)
    elif action == 'exercise':
        return exercise_handler(open_id, req)
    elif action == 'reco_object':
        return reco_object_handler(open_id, req)
    elif action == 'reco_ocr':
        return reco_ocr_handler(open_id, req)
    elif action == 'reco_face':
        return reco_face_handler(open_id, req)
    elif action == 'profile':
        return profile_handler(open_id, req)
    
    return jsonify({'error': 'action parameter is not supported yet'}), 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
