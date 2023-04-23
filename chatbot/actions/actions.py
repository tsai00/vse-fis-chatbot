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


class ActionDetectLanguage(Action):
    def name(self) -> Text:
        return "action_detect_language"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        languages = {
            'Czech': 'cs',
            'English': 'en'
        }

        text = tracker.latest_message.get('text')

        # Additional entity "language" is used, so not to overwrite langname / langcode
        language = tracker.get_slot('language')

        # Language might be already set (e.g. in payload)
        if language is None:
            try:
                result = Detector(text).language
                langcode = result.code
                langname = result.name
            except:
                langcode = 'cs'
                langname = 'Czech'
        else:
            langcode = languages.get(language)
            langname = language

        if langcode not in ['en', 'cs']:
            dispatcher.utter_message(
                text=f'Unfortunately I don\'t speak {langcode}, can only speak English or Czech')

        print(langname)

        return [SlotSet("langcode", langcode), SlotSet("langname", langname), SlotSet("language", None)]


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

        bachelor_programs = '<br> \u2022 ' + '<br> \u2022 '.join(json_dict['bachelor'])
        master_programs = '<br> \u2022 ' + '<br> \u2022 '.join(json_dict['master'])
        doctor_programs = '<br> \u2022 ' + '<br> \u2022 '.join(json_dict['doctor'])

        print(json_dict['master'])
        print(master_programs)

        if all([bachelor_degree is None, master_degree is None, doctor_degree is None]):
            if language == 'cs':
                message = f"FIS momentálně nabízí následující programy: <br>Bachelor: {bachelor_programs}<br>" + f"Master: {master_programs}<br>" + f"PhD: {doctor_programs}"
            else:
                message = f"FIS currently offers following programs: <br>Bachelor: {bachelor_programs}<br>" + f"Master: {master_programs}<br>" + f"PhD: {doctor_programs}"
        else:
            message = ''
            if bachelor_degree is not None:
                if language == 'cs':
                    message = f'FIS momentálně nabízí následující bakalářské programy: <br>{bachelor_programs}'
                else:
                    message = f'For Bachelor students FIS currently offers following programs: <br>{bachelor_programs}'
            if master_degree is not None:
                if language == 'cs':
                    message = f'FIS momentálně nabízí následující magisterské programy: <br>{master_programs}'
                else:
                    message = f'For Master students FIS currently offers following programs: <br>{master_programs}'
            if doctor_degree is not None:
                if language == 'cs':
                    message = f'FIS momentálně nabízí následující doktorské programy: <br>{doctor_programs}'
                else:
                    message = f'For PhD students FIS currently offers following programs: <br>{doctor_programs}'

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

        dispatcher.utter_message(text="Ahoj, jsem FISBot, virtuální asistent a rád ti poradím. Napíš, co by tě zajímalo. <br>"
                                      "Mluvím česky a anglicky. Můžeš se přepínat mezi jazyky přímo během konverzace.<br>"
                                      "Pamatuj si ale prosím, že se jen učím a nejsem Chat GPT-5 :)")

        button_resp = [
            {"title": "Bakalářské studium", "payload": '/study_programs{"bachelor_degree": "bakalářské", "language": "Czech"}'},
            {"title": "Magisterské studium", "payload": '/study_programs{"master_degree": "magisterské", "language": "Czech"}'},
            {"title": "Doktorské studium", "payload": '/study_programs{"doctor_degree": "doktorksé", "language": "Czech"}'},
        ]

        dispatcher.utter_message(text="Nevíš, jak se zeptat? Tady jsme pro tebe připravili nejčastější okruhy otázek.", buttons=button_resp)

        return []


class ActionDefaultAskAffirmation(Action):
    def name(self):
        return "action_default_ask_affirmation"
    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):

        language = tracker.get_slot('langcode')

        if language not in ['en', 'cs']:
            language = 'cs'

        # Select top 3 intents from the tracker + skip 1st one (nlu fallback)
        predicted_intents = tracker.latest_message["intent_ranking"][1:4]

        if language == 'cs':
            # Show user-friendly translation of most popular intents
            intent_mappings = {
                "study_programs": "Studijní programy",
                "holiday": "Kdo má svátek dneska?",
                "canteen_menu": "Jidelníček na dnes",
            }

            message = "Promiň, nerozumím ti. Máš na mýsli něco z tohohle?"
        else:
            # Show user-friendly translation of most popular intents
            intent_mappings = {
                "study_programs": "Study programs",
                "holiday": "Who has holiday today?",
                "canteen_menu": "Canteen menu",
            }

            message = "Sorry, can not understand you. What do you want to do?"

        default_button_titles = {
            'cs': 'Jiné',
            'en': 'Other'
        }

        out_of_scope_path = f'out_of_scope{{"language": "{"Czech" if language == "cs" else "English"}"}}'
        buttons_all = [
            {
                "title": intent_mappings.get(intent['name'], default_button_titles[language]),
                "payload": f"/{intent['name'] if intent_mappings.get(intent['name'], default_button_titles[language]) not in default_button_titles.values() else out_of_scope_path}"
            }
            for intent in predicted_intents
        ]

        # Keep unique buttons (based on title) only
        buttons_unique = list({v['title']: v for v in buttons_all}.values())

        buttons_sorted = []
        button_default = None

        # Ensure default button is last
        for button in buttons_unique:
            if button['title'] in default_button_titles.values():
                button_default = button
            else:
                buttons_sorted.append(button)

        buttons_sorted.append(button_default)

        dispatcher.utter_message(text=message, buttons=buttons_sorted)

        return []


class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        language = tracker.get_slot('langcode')

        if language not in ['en', 'cs']:
            language = 'cs'

        if language == 'cs':
            message = f"Promiň, ale s tímhle ti pomoct nemůžu. Zkus se prosím obratit na studijní oddělení: <br>" \
                      f"\u2022 Bakalářské studium: jana.hudcekova@vse.cz, sedlacko@vse.cz <br>" \
                      f"\u2022 Magisterské studium:  iva.hudcova@vse.cz, veronika.brunerova@vse.cz <br>" \
                      f"\u2022 Doktorské studium: tereza.krajickova@vse.cz<br>"
        else:
            message = f"I'm sorry, I can't help you with that. Please contact student office: <br>" \
                      f"\u2022 Bachelor studies: jana.hudcekova@vse.cz, sedlacko@vse.cz <br>" \
                      f"\u2022 Master studies:  iva.hudcova@vse.cz, veronika.brunerova@vse.cz <br>" \
                      f"\u2022 Doctoral studies: tereza.krajickova@vse.cz <br>"

        # tell the user they are being passed to a customer service agent
        dispatcher.utter_message(text=message)

        # pause the tracker so that the bot stops responding to user input
        return [ConversationPaused(), UserUtteranceReverted()]


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

        try:
            menu_df = pd.DataFrame(todays_menu)
            menu_df['mealName'] = menu_df.apply(lambda x: [x['rows'][i]['item']['mealName'] for i in range(len(x['rows']))], axis=1)
        except:
            todays_menu = ''

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