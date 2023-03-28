import random

from flask import Flask, request, jsonify
import logging
import requests
import json


app = Flask(__name__)


logging.basicConfig(level=logging.INFO)

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    return jsonify(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']
    user_answer = req['request']['original_utterance'].lower()
    if req['session']['new']:
        # sessionStorage['quizzes'] = requests.get('http://адрес нашего сайта/api/quiz').json()['quiz']
        with open('all_quizzes.json', 'r') as file:
            sessionStorage['quizzes'] = json.load(file)

        sessionStorage[user_id]['status'] = 'start'
        greet = greeting()
        res['response']['text'] = greet['text']
        res['response']['buttons'] = greet['buttons']
        return
    if sessionStorage[user_id]['status'] == 'start':

        if user_answer == "да, давай" or req['request']['nlu']['intents']['YANDEX.CONFIRM']:
            random_quiz(user_id)
            passing_the_quiz(req, res)
        elif user_answer == 'нет' or req['request']['nlu']['intents']['YANDEX.REJECT']:
            res['response']['text'] = 'Хорошо, тогда можешь посмотреть топ викторин'
            res['response']['card'] = show_top()['card']
        elif user_answer == 'что ты можешь?':
            res['response']['text'] = '''Я могу запустить случайную или выбранную тобой викторину, 
            могу вывести топ самых проходимых. А если ты не нашел той викторины, которую хотел пройти,  
            можешь сам ее создать'''
            res['response']['buttons'] = get_idle_suggests()
            sessionStorage[user_id]['status'] = 'idling'
        elif user_answer == 'расскажи правила' or user_answer == 'помощь':
            res['response']['text'] = '''Викторины состоят из нескольких вопросов, в ответ на каждый ты
             можешь выбрать один вариант из нескольких предложенных. Ответив на каждый вопрос, ты узнаешь результат'''
            res['response']['buttons'] = get_idle_suggests()
            sessionStorage[user_id]['status'] = 'idling'
        else:
            res['response']['text'] = unrecognized_phrase()['text']
        return
    if sessionStorage[user_id]['status'] == 'passing_the_quiz':
        if user_answer in ['выход', 'стоп']:
            res['response']['text'] = 'Хорошо, выхожу из викторины'
            sessionStorage[user_id]['status'] = 'idling'
        else:
            passing_the_quiz(req, res)
        return
    if sessionStorage[user_id]['status'] == 'idling':
        if user_answer == 'выведи топ викторин':
            show_top()
        elif 'запусти викторину' in user_answer:
            sessionStorage[user_id]['current_quiz'] = user_answer.split('запусти викторину')[-1].strip()
            sessionStorage[user_id]['status'] = 'passing_the_quiz'
            sessionStorage[user_id]['current_question'] = 0
            passing_the_quiz(req, res)
        elif user_answer == 'запусти случайную викторину':
            random_quiz(user_id)
        elif user_answer == 'я хочу создать викторину':
            create_quiz()
        elif user_answer == 'что ты можешь?':
            res['response']['text'] = '''Я могу запустить случайную или выбранную тобой викторину, 
            могу вывести топ самых проходимых. А если ты не нашел той викторины, которую хотел пройти,  
            можешь сам ее создать'''
            res['response']['buttons'] = get_idle_suggests()
        elif user_answer == 'расскажи правила':
            res['response']['text'] = '''Викторины состоят из нескольких вопросов, в ответ на каждый ты
             можешь выбрать один вариант из нескольких предложенных. Ответив на каждый вопрос, ты узнаешь результат'''
            res['response']['buttons'] = get_idle_suggests()

def get_idle_suggests():
    result = {
         'buttons': [
        {
            "title": "Выведи топ викторин",
            "payload": {},
            "hide": True
        },
             {
                 "title": "Запусти случайную викторину",
                 "payload": {},
                 "hide": True
             },
             {
                 "title": "Я хочу создать викторину",
                 "payload": {},
                 "hide": True
             },
             {
                 "title": "Что ты можешь?",
                 "payload": {},
                 "hide": True
             },
             {
                 "title": "Расскажи правила",
                 "payload": {},
                 "hide": True
             }


         ]
     }
    return result


def create_quiz():
    return


def unrecognized_phrase():
    result = {
        'text': 'Извини, я тебя не поняла, повтори пожалуйста'
    }
    return result


def show_top():
    result = {
        'card': {
            'type' : 'ItemList',
            "header": {
                "text": "Заголовок списка изображений",
            },
            'items': []
        },
        'buttons': [
            {
                "title": "Викторина 1",
                "payload": {},
                "hide": True
            },
            {
                "title": "Викторина 2",
                "payload": {},
                "hide": True
            }
        ]


    }
    return result


def passing_the_quiz(req, res):
    # TODO: загрузку фото и кнопки вариантов ответов
    # Для прохождения нужно id квиза и № вопроса
    # Храним их в sessionStorage
    user_id = req['session']['user_id']
    session = sessionStorage[user_id]
    quiz_id = ['current_quiz']
    quest_numb = session['current_question']
    quiz = sessionStorage['quizzes'][quiz_id]
    if quest_numb == 0:
        res['response']['text'] = f"""{quiz['title']}\n\n{quiz['description']}\n от {quiz['creator']}"""
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Где выводится это сообщение?'
        res['response']['card']['image_id'] = 'id картинки'
        if quiz['type'] == 'percent':
            session['result'] = 0
        else:
            session['result'] = {}
            for pers in quiz['characters']:
                session['result'][pers['title']] = 0
    elif quest_numb <= len(quiz['questions']):
        question = quiz['questions'][quest_numb - 1]
        answers = '\n'.join([f"{i + 1}. {value['title']}" for i, value in question['answers']])
        res['response']['text'] = f"""{question['title']}\n\n{answers}"""
    else:
        if quiz['type'] == 'person':
            result = max(session['result'].values())
            for key, value in session['result'].items():
                if value == result:
                    result = key
                    break
            result = list(filter(lambda x: x['title'] == result, quiz['characters']))[0]
            res['response']['text'] = f"""Поздравляем! Вы - {result['title']}!\n{result['description']}"""
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Ваш персонаж'
            res['response']['card']['image_id'] = 'id картинки'
        else:
            res['response']['text'] = f"""Поздравляем! Вы ответили правильно на {int(100 * session['result'] / len(quiz['questions']))}%"""

    if 1 <= quest_numb <= len(quiz['questions']):
        answer = int(req['request']['original_utterance']) # id + 1 ответа
        if quiz['type'] == 'percent':
            if quiz['questions'][quest_numb - 2]['answers'][answer - 1]['is_true']:
                session['result'] += 1
        else:
            for pers in quiz['questions'][quest_numb - 2]['answers'][answer - 1]['characters']:
                session['result'][pers] += 1

    session['current_question'] += 1
    sessionStorage[user_id] = session
    return


def random_quiz(user_id):
    sessionStorage[user_id]['status'] = 'passing_the_quiz'
    sessionStorage[user_id]['current_quiz'] = random.randint(0, len(sessionStorage['quizzes']))
    sessionStorage[user_id]['current_question'] = 0
    return


def download_image_by_bits(image_bits):
    alice_url = 'https://dialogs.yandex.net/api/v1/skills/a9331dba-12d5-41be-ba3b-d691a6294153/images'
    headers = {'Authorization': 'OAuth y0_AgAAAAAhKRZBAAT7owAAAADfkTMUOctm8BgkQU-3pQ8X_Vd5UK3G1qw'}
    files = {'file': image_bits}
    req = requests.post(url=alice_url, headers=headers, files=files)
    return req.json()


def delete_image(image_id):
    alice_url = f'https://dialogs.yandex.net/api/v1/skills/a9331dba-12d5-41be-ba3b-d691a6294153/images/{image_id}'
    headers = {'Authorization': 'OAuth y0_AgAAAAAhKRZBAAT7owAAAADfkTMUOctm8BgkQU-3pQ8X_Vd5UK3G1qw'}
    req = requests.delete(url=alice_url, headers=headers)
    return req.json()


def greeting():
    result = {
        'text': '''
    Привет! Я управляющая викторинами ЯQuiz. У меня есть викторины для всех и каждого. Начнем случайную викторину?
    ''',
        'buttons': [
            {
            "title": "Да, давай",
            "payload": {},
            "hide": True
            },
            {
                "title": "Нет",
                "payload": {},
                "hide": True
            }
        ]

    }
    return result

if __name__ == '__main__':
    app.run()