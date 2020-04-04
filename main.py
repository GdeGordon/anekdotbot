import requests
import re
import logging
import argparse
from collections import namedtuple
from time import sleep
from random import randint


def get_random_story():
    i = randint(1, 4000)
    r = requests.get(f'https://vse-shutochki.ru/istorya/{i}')
    anec = re.findall(r'.*<div class=\"post\">(.*)', r.text)[0].replace('<br>', '\n')
    return anec

def get_random_anec_id():
    r = requests.get('https://vse-shutochki.ru/anekdoty')
    anec_id = re.findall('<a href=\"\/anekdot/(\d+)', r.text)[0]
    return anec_id

def get_anec(anec_id):
    r = requests.get(f'https://vse-shutochki.ru/anekdot/{anec_id}')
    anec = re.findall(r'.*<div class=\"post\">(.*)', r.text)[0].replace('<br>', '\n')
    return anec

def send_message(peer_id, reply_to, text, oauth_token):
    random_id = randint(0, 9223372036854775807)
    logging.info(f'sending message {text} to {peer_id}')
    r = requests.get(f'https://api.vk.com/method/messages.send?v=5.103&random_id={random_id}&reply_to={reply_to}&peer_id={peer_id}&message={text}&access_token={oauth_token}')

def send_anec(peer_id, reply_to, oauth_token):
    text = get_anec(get_random_anec_id())
    send_message(peer_id, reply_to, text, oauth_token)

def send_story(peer_id, reply_to, oauth_token):
    text = get_random_story()
    send_message(peer_id, reply_to, text, oauth_token)

def handle(response, oauth_token):
    updates = response.get('updates')
    logging.info(f'handling {len(updates)} events')
    for update in response.get('updates'):
        if update['type'] == 'message_new':
            message_text = update['object']['message']['text'].lower()
            message_id = update['object']['message']['id']
            peer_id = update['object']['message']['peer_id']
            if ('ефим' in message_text and 'анекдот' in message_text):
                send_anec(peer_id, message_id, oauth_token)
            elif ('ефим' in message_text and 'история' in message_text):
                send_story(peer_id, message_id, oauth_token)

def get_polling_server(group_id, oauth_token):
    logging.info(f'getting polling server for group_id {args.group_id}')
    info = namedtuple('info', ['key', 'server', 'ts'])
    r = requests.get(f'https://api.vk.com/method/groups.getLongPollServer?v=5.103&group_id={group_id}&access_token={oauth_token}').json()
    key = r['response']['key']
    server = r['response']['server']
    ts = r['response']['ts']
    return info(key=key, server=server, ts=ts)

def polling(polling_info, oauth_token):
    logging.info(f'starting polling for group id {args.group_id}')
    key = polling_info.key
    server = polling_info.server
    ts = polling_info.ts
    while True:
        r = requests.get(f'{server}?act=a_check&key={key}&ts={ts}&wait=5').json()
        handle(r, oauth_token)
        ts = r['ts']


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', help='oauth token')
    parser.add_argument('--group_id', help='group id')
    args = parser.parse_args()
    logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s', level=logging.INFO)
    polling_info = get_polling_server(args.group_id, args.token)
    polling(polling_info, args.token)


