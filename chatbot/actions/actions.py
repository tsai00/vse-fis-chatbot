import datetime
from typing import Any, Text, Dict, List
import requests
import json
import pandas as pd
from pathlib import Path
from rasa_sdk import Action, Tracker
from rasa_sdk.events import ConversationPaused
from rasa_sdk.events import UserUtteranceReverted
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from polyglot.detect import Detector


LANGUAGES = {
    'cs': 'Czech',
    'en': 'English'
}


class ActionDetectLanguage(Action):
    def name(self) -> Text:
        return "action_detect_language"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        text = tracker.latest_message.get('text')
        langcode = tracker.get_slot('langcode')     # Language might be already set (e.g. in payload)
        print(langcode)

        if langcode is None:
            print(text)

            try:
                result = Detector(text).language
                langcode = result.code
                langname = result.name
            except:
                langcode = 'cs'
                langname = 'Czech'
        else:
            langname = LANGUAGES.get(langcode)

        if langcode not in ['en', 'cs']:
            dispatcher.utter_message(
                text=f'Unfortunately I can not speak {langcode}, but can only speak English or Czech')

        print(langname)

        return [SlotSet("langcode", langcode), SlotSet("langname", langname)]


class ActionStudyPrograms(Action):

    def name(self) -> Text:
        return "action_study_programs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        language = tracker.get_slot('langcode')

        if language not in ['en', 'cs']:
            language = 'cs'

        bachelor_degree = next(tracker.get_latest_entity_values('bachelor_degree'), None)
        master_degree = next(tracker.get_latest_entity_values('master_degree'), None)
        doctor_degree = next(tracker.get_latest_entity_values('doctor_degree'), None)

        study_programs_file = Path(Path(__file__).resolve().parent, 'sources', f'programs_{language}.json')

        with study_programs_file.open(mode='r') as f:
            json_dict = json.load(f)

        print(bachelor_degree)
        print(master_degree)
        print(doctor_degree)

        bachelor_programs = '\n\u2022' + '\n\u2022 '.join(json_dict['bachelor'])
        master_programs = '\n\u2022' + '\n\u2022 '.join(json_dict['master'])
        doctor_programs = '\n\u2022' + '\n\u2022 '.join(json_dict['doctor'])

        print(json_dict['master'])
        print(master_programs)

        if all([bachelor_degree is None, master_degree is None, doctor_degree is None]):
            if language == 'cs':
                message = f"FIS momentálně nabízí následující programy: \nBachelor: {bachelor_programs}\n" + f"Master: {master_programs}\n" + f"PhD: {doctor_programs}\n"
            else:
                message = f"FIS currently offers following programs: \nBachelor: {bachelor_programs}\n" + f"Master: {master_programs}\n" + f"PhD: {doctor_programs}\n"
        else:
            message = ''
            if bachelor_degree is not None:
                if language == 'cs':
                    message = f'FIS momentálně nabízí následující bakalářské programy:\n {bachelor_programs}'
                else:
                    message = f'For Bachelor students FIS currently offers following programs:\n {bachelor_programs}'
            if master_degree is not None:
                if language == 'cs':
                    message = f'FIS momentálně nabízí následující magisterské programy:\n {master_programs}'
                else:
                    message = f'For Master students FIS currently offers following programs:\n {master_programs}'
            if doctor_degree is not None:
                if language == 'cs':
                    message = f'FIS momentálně nabízí následující doktorské programy:\n {doctor_programs}'
                else:
                    message = f'For PhD students FIS currently offers following programs:\n {doctor_programs}'

        dispatcher.utter_message(text=message)

        return []


class ActionGetHoliday(Action):

    def _get_todays_holiday(self):
        # TODO: extend for other days than today
        holidays_api_url = 'https://svatkyapi.cz/api'
        try:
            response = requests.get(f'{holidays_api_url}/day')
            name = response.json()['name']
        except:
            name = None

        return name

    def name(self) -> Text:
        return "action_get_holiday"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        language = tracker.get_slot('langcode')
        todays_holiday = self._get_todays_holiday()

        if language == 'cs':
            if todays_holiday is not None:
                message = f'Dneska má svátek {todays_holiday}'
            else:
                message = 'Momentálně ti bohužel nemůžeme říct, kdo má dneska svátek. Ale dejme tomu, že dneska mají svátek všichni :)'
        else:
            if todays_holiday is not None:
                message = f'{todays_holiday} has holiday today'
            else:
                message = 'Unfortunately we can\'t say who has holiday today. But let\'s say today is everybody\'s holiday :)'

        dispatcher.utter_message(text=message)

        return []


class ActionIntroMessage(Action):

    def name(self) -> Text:
        return "action_intro_message"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Ahoj, jsem FISBot, virtuální asistent a rád ti poradím. Napíš, co by tě zajímalo. \n"
                                      "Mluvím česky a anglicky. Můžeš se přepínat mezi jazyky přímo během konverzace.\n"
                                      "Pamatuj se ale prosím, že se jen učím a nejsem Chat GPT-5 :)")

        button_resp = [
            #{"title": "Bakalářské studium", "payload":"/study_programs{/"master_degree/":/"magisterské/"/"slot2/":/"value2/"}},
            {"title": "Magisterské studium", "payload": '/study_programs{"master_degree": "magisterské", "langcode": "cs"}'},
            {"title": "Doktorské studium", "payload": '/study_programs{"langcode": ' + f'"cs"' + '}'},
        ]

        dispatcher.utter_message(text="Nevíš, jak se zeptat? Tady jsme pro tebe připravili nejčastější okruhy otázek.", buttons=button_resp)

        return []


class ActionGetCanteenMenu(Action):
    def _get_menu(self):
        headers = {
            'Accept': 'application/json',
            'Cookie': 'Anete2=585c60bb-43ac-45d7-804c-df13fd845a0d; vse_cookie_allow=%5B%5D; vse_cookie_set=1',
            'Referer': 'https://webkredit.vse.cz/webkredit_italska/Ordering/Menu',
            'Host': 'webkredit.vse.cz',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15',
            'Accept-Language': 'cs',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'X-Requested-With': 'XMLHttpRequest'
        }

        today = f'{datetime.datetime.now():%Y-%m-%d}'
        today = '2023-04-24'
        canteen_menu_url = f'https://webkredit.vse.cz/webkredit_italska/Api/Ordering/Menu?Dates={today}T00%3A00%3A00.000Z&CanteenId=1'
        try:
            response = requests.get(canteen_menu_url, headers=headers)
            menu = response.json()['groups']
        except:
            menu = None

        return menu

    def name(self) -> Text:
        return "action_get_canteen_menu"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        language = tracker.get_slot('langcode')

        todays_menu = self._get_menu()

        menu_df = pd.DataFrame(todays_menu)

        menu_df['mealName'] = menu_df.apply(lambda x: [x['rows'][i]['item']['mealName'] for i in range(len(x['rows']))], axis=1)

        if todays_menu:
            message = ''

            if language == 'cs':
                message += 'Dneska v menze mají: <br><br>'
            else:
                message += 'Today\'s menu in canteen: <br><br>'

            for _, row in menu_df.iterrows():
                message += row['mealKindName'] + '<br>'
                message += ' \u2022 ' + '<br> \u2022 '.join(row['mealName']) + '<br><br>'
        elif not todays_menu:
            if language == 'cs':
                message = 'Jídelníček na dneska není k dispozici'
            else:
                message = 'There is no canteen menu for today'
        else:
            if language == 'cs':
                message = 'Momentálně ti bohužel nemůžeme ukázat jídelníček'
            else:
                message = 'Unfortunately we could not provide you with menu canteen at the moment'

        print(message)
        dispatcher.utter_message(text=message)

        return []