from typing import Any, Text, Dict, List
import requests
import json
from pathlib import Path
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionStudyPrograms(Action):

    def name(self) -> Text:
        return "action_study_programs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        bachelor_degree = next(tracker.get_latest_entity_values('bachelor_degree'), None)
        master_degree = next(tracker.get_latest_entity_values('master_degree'), None)
        doctor_degree = next(tracker.get_latest_entity_values('doctor_degree'), None)

        STUDY_PROGRAMS_LOCATION_EN = Path(Path(__file__).resolve().parent, '..', '..', 'sources', 'programs_en.json')

        with STUDY_PROGRAMS_LOCATION_EN.open(mode='r') as f:
            json_dict = json.load(f)

        print(bachelor_degree)
        print(master_degree)
        print(doctor_degree)

        if all([bachelor_degree is None, master_degree is None, doctor_degree is None]):
            message = f"FIS currently offers following programs: \nBachelor: {json_dict['bachelor']}\n" + f"Master: {json_dict['master']}\n" + f"PhD: {json_dict['doctor']}\n"
        else:
            message = ''
            if bachelor_degree is not None:
                message = f'For Bachelor students FIS currently offers following programs:\n {json_dict["bachelor"]}'
            if master_degree is not None:
                message = f'For Master students FIS currently offers following programs:\n {json_dict["master"]}'
            if doctor_degree is not None:
                message = f'For PhD students FIS currently offers following programs:\n {json_dict["doctor"]}'

        dispatcher.utter_message(text=message)

        return []


class ActionGetHoliday(Action):

    def _get_todays_holiday(self):
        # TODO: extend for other days than today
        holidays_api_url = 'https://svatkyapi.cz/api'
        try:
            response = requests.get(f'{holidays_api_url}/day')
            name = response.json()['name']
            message_cz = f'Dneska má svátek {name}'
        except:
            message_cz = 'Momentálně ti bohužel nemůžeme říct, kdo má dneska svátek. Ale dejme tomu, že dneska mají svátek všichni :)'

        return message_cz

    def name(self) -> Text:
        return "action_get_holiday"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text=self._get_todays_holiday())

        return []
