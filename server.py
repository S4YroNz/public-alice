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
    user_answer = req['request']['nlu']['intents']
    if req['session']['new']:
        # sessionStorage['quizzes'] = requests.get('http://адрес нашего сайта/api/quiz').json()['quiz']
        with open('all_quizzes.json', 'r') as file:
            sessionStorage['quizzes'] = json.load(file)
        sessionStorage[user_id] = {}
        sessionStorage[user_id]['status'] = 'start'
        greet = greeting()
        res['response']['text'] = greet['text']
        res['response']['tts'] = greet['text']
        res['response']['buttons'] = greet['buttons']
        return
    if sessionStorage[user_id]['status'] == 'start':

        if 'YANDEX.CONFIRM' in user_answer:
            random_quiz(user_id)
            passing_the_quiz(req, res)
        elif 'YANDEX.REJECT' in user_answer:
            res['response']['tts'] = 'Хорошо, тогда можешь посмотреть топ викторин'
            res['response']['text'] = 'Хорошо, тогда можешь посмотреть топ викторин'
            res['response']['card'] = show_top()['card']
            sessionStorage[user_id]['status'] = 'idling'
        elif 'WHAT_YOU_CAN_DO' in user_answer:
            res['response']['text'] = '''Я могу запустить случайную или выбранную тобой викторину, 
            могу вывести топ самых проходимых. А если ты не нашел той викторины, которую хотел пройти,  
            можешь сам ее создать'''
            res['response']['tts'] = '''Я могу запустить случайную или выбранную тобой викторину, 
                        могу вывести топ самых проходимых. А если ты не нашел той викторины, которую хотел пройти,  
                        можешь сам ее создать'''
            res['response']['buttons'] = get_idle_suggests()['buttons']
            sessionStorage[user_id]['status'] = 'idling'
        elif 'YANDEX.HELP' in user_answer:
            res['response']['text'] = '''Викторины состоят из нескольких вопросов, в ответ на каждый ты
             можешь выбрать один вариант из нескольких предложенных. Ответив на каждый вопрос, ты узнаешь результат'''
            res['response']['tts'] = '''Викторины состоят из нескольких вопросов, в ответ на каждый ты
                         можешь выбрать один вариант из нескольких предложенных. Ответив на каждый вопрос, ты узнаешь результат'''
            res['response']['buttons'] = get_idle_suggests()['buttons']
            sessionStorage[user_id]['status'] = 'idling'
        else:
            unrec_phrase = unrecognized_phrase()
            res['response']['text'] = unrec_phrase['text']
            res['response']['tts'] = unrec_phrase['text']

            res['response']['buttons'] = get_idle_suggests()['buttons']

        return

    if sessionStorage[user_id]['status'] == 'passing_the_quiz':
        if 'STOP' in user_answer:
            res['response']['text'] = 'Хорошо, выхожу из викторины'
            res['response']['tts'] = 'Хорошо, выхожу из викторины'
            sessionStorage[user_id]['status'] = 'idling'
        else:
            passing_the_quiz(req, res)
        return



    if sessionStorage[user_id]['status'] == 'idling':
        if 'SHOW_TOP' in user_answer:
            res['response']['tts'] = 'Окей, вот текущий топ викторин'
            res['response']['text'] = 'Окей, вот текущий топ викторин'
            res['response']['card'] = show_top()['card']
        elif 'START_QUIZ' in user_answer:
            quiz_title = user_answer['START_QUIZ']['slots']['quiz_title']['value']
            sessionStorage[user_id]['current_quiz'] = user_answer.split('запусти викторину')[-1].strip()
            sessionStorage[user_id]['status'] = 'passing_the_quiz'
            sessionStorage[user_id]['current_question'] = 0
            passing_the_quiz(req, res)
        elif 'START_RANDOM_QUIZ' in user_answer:
            random_quiz(user_id)
        elif 'CREATE_QUIZ' in user_answer:
            create_quiz()
        elif 'WHAT_YOU_CAN_DO' in user_answer:
            res['response']['text'] = '''Я могу запустить случайную или выбранную тобой викторину, 
            могу вывести топ самых проходимых. А если ты не нашел той викторины, которую хотел пройти,  
            можешь сам ее создать'''
            res['response']['tts'] = '''Я могу запустить случайную или выбранную тобой викторину, 
                        могу вывести топ самых проходимых. А если ты не нашел той викторины, которую хотел пройти,  
                        можешь сам ее создать'''
            res['response']['buttons'] = get_idle_suggests()['buttons']
        elif 'YANDEX.HELP' in user_answer:
            res['response']['text'] = '''Викторины состоят из нескольких вопросов, в ответ на каждый ты
             можешь выбрать один вариант из нескольких предложенных. Ответив на каждый вопрос, ты узнаешь результат'''
            res['response']['tts'] = '''Викторины состоят из нескольких вопросов, в ответ на каждый ты
                         можешь выбрать один вариант из нескольких предложенных. Ответив на каждый вопрос, ты узнаешь результат'''
            res['response']['buttons'] = get_idle_suggests()['buttons']
        elif 'STOP' in user_answer:
            res['response']['text'] = 'Пока, возвращайся еще'
            res['response']['tts'] = 'Пока, возвращайся еще'
            res['response']['end_session'] = True
        else:
            unrec_phrase = unrecognized_phrase()
            res['response']['text'] = unrec_phrase['text']
            res['response']['tts'] = unrec_phrase['text']

            res['response']['buttons'] = get_idle_suggests()['buttons']

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
                 "title": "Помощь",
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
            'type': 'ItemsList',
            "header":
            {
                "text": "Текущий топ викторин",
            },
            'items':
                [
                    {
                        "title": "Викторина 1",
                        "description": "Классная викторина",
                        "button":
                        {
                            "text": "Выбрать первый вариант",
                            "payload": {}
                        }
                    }
                ],
            "footer": {
                "text": "Выбери викторину, и я ее запущу",
            }
            },

        'buttons': []


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