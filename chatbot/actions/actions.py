from typing import Any, Text, Dict, List
import requests
import json
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