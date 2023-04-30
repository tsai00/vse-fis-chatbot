import datetime
from typing import Any, Text, Dict, List
import requests
import json
import pandas as pd
import os
import redis
import difflib
import pyarrow as pa

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from dotenv import load_dotenv
from pathlib import Path
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import ConversationPaused
from rasa_sdk.events import UserUtteranceReverted
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.types import DomainDict
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
                text=f'Unfortunately I don\'t speak {langname}, can only speak English or Czech')

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
            if language == 'en':
                message = f"FIS currently offers following programs: <br>Master: {master_programs}<br>" + f"PhD: {doctor_programs}"
            else:
                message = f"FIS momentálně nabízí následující programy: <br>Bakalářské: {bachelor_programs}<br>" + f"Magisterské: {master_programs}<br>" + f"Doktorské: {doctor_programs}"

        else:
            message = ''
            if bachelor_degree is not None:
                if language == 'en':
                    message = f'Unfortunately FIS does not currently offer any Bachelor program in English.'
                else:
                    message = f'FIS momentálně nabízí následující bakalářské programy: <br>{bachelor_programs}'

            if master_degree is not None:
                if language == 'en':
                    message = f'For Master students FIS currently offers following programs: <br>{master_programs}'
                else:
                    message = f'FIS momentálně nabízí následující magisterské programy: <br>{master_programs}'

            if doctor_degree is not None:
                if language == 'en':
                    message = f'For PhD students FIS currently offers following programs: <br>{doctor_programs}'
                else:
                    message = f'FIS momentálně nabízí následující doktorské programy: <br>{doctor_programs}'

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

        if language == 'en':
            if todays_holiday is not None:
                message = f'{todays_holiday} has holiday today'
            else:
                message = 'Unfortunately we can\'t say who has holiday today. But let\'s say today is everybody\'s holiday :)'
        else:
            if todays_holiday is not None:
                message = f'Dneska má svátek {todays_holiday}'
            else:
                message = 'Momentálně ti bohužel nemůžeme říct, kdo má dneska svátek. Ale dejme tomu, že dneska mají svátek všichni :)'

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
            {"title": "Bakalářské obory", "payload": '/study_programs{"bachelor_degree": "bakalářské", "language": "Czech"}'},
            {"title": "Magisterské obory", "payload": '/study_programs{"master_degree": "magisterské", "language": "Czech"}'},
            {"title": "Doktorské obory", "payload": '/study_programs{"doctor_degree": "doktorksé", "language": "Czech"}'},
            {"title": "Hledat konzultační hodiny", "payload": '/consulting_hours{"language": "Czech"}'},
            {"title": "Dnešní jídelníček", "payload": '/canteen_menu{"language": "Czech"}'},
            {"title": "Mapa budov", "payload": '/buildings_map'},
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

        if language == 'en':
            # Show user-friendly translation of most popular intents
            intent_mappings = {
                "study_programs": "Study programs",
                "holiday": "Who has holiday today?",
                "canteen_menu": "Canteen menu",
                "accommodation": "Accommodation",
                "student_unity": "Student unity",
                "consulting_hours": "Consulting hours",
                "events": "Events",
                "academic_year_schedule": "Academic year schedule",
                "addresses": "Addresses",
                "scholarship": "Scholarship",
                "tuition_fee": "Tuition fee",
                "video_manuals": "Video manuals",
                "credit_system": "ECTS system",
                "buildings_map": "Buildings map",
            }

            message = "Sorry, can not understand you. What do you want to do?"
        else:
            # Show user-friendly translation of most popular intents
            intent_mappings = {
                "study_programs": "Studijní programy",
                "holiday": "Kdo má svátek dneska?",
                "canteen_menu": "Jidelníček na dnes",
                "accommodation": "Ubytování",
                "student_unity": "Studentské spolky",
                "consulting_hours": "Konzultační hodiny",
                "events": "Akce",
                "academic_year_schedule": "Harmonogram",
                "addresses": "Adresy budov",
                "scholarship": "Stipendia",
                "tuition_fee": "Poplatky za studium",
                "video_manuals": "Video příručky",
                "credit_system": "Kreditový systém",
                "buildings_map": "Mapa budov",
            }

            message = "Promiň, nerozumím ti. Máš na mysli něco z tohohle?"

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

        if language == 'en':
            message = f"I'm sorry, I can't help you with that. Please contact student office: <br>" \
                      f"\u2022 Bachelor studies: jana.hudcekova@vse.cz, sedlacko@vse.cz <br>" \
                      f"\u2022 Master studies:  iva.hudcova@vse.cz, veronika.brunerova@vse.cz <br>" \
                      f"\u2022 Doctoral studies: tereza.krajickova@vse.cz <br>"
        else:
            message = f"Promiň, ale s tímhle ti pomoct nemůžu. Zkus se prosím obratit na studijní oddělení: <br>" \
                      f"\u2022 Bakalářské studium: jana.hudcekova@vse.cz, sedlacko@vse.cz <br>" \
                      f"\u2022 Magisterské studium:  iva.hudcova@vse.cz, veronika.brunerova@vse.cz <br>" \
                      f"\u2022 Doktorské studium: tereza.krajickova@vse.cz<br>"


        # tell the user they are being passed to a customer service agent
        dispatcher.utter_message(text=message)

        # pause the tracker so that the bot stops responding to user input
        return [ConversationPaused(), UserUtteranceReverted()]


class ActionGetCanteenMenu(Action):
    def _get_menu(self, date):
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

        canteen_menu_url = f'https://webkredit.vse.cz/webkredit_italska/Api/Ordering/Menu?Dates={date}T00%3A00%3A00.000Z&CanteenId=1'
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

        today = f'{datetime.datetime.now():%Y-%m-%d}'
        today = '2023-05-01'

        # First check if menu from today does not already exist in Redis (to avoid unnecessary requests)
        # Note: chatbot_redis is name of Docker container from docker compose
        r = redis.Redis(host='localhost', port=6379, encoding="utf-8", decode_responses=True, db=0)

        redis_canteen_value = r.get(f'canteen_menu_{today}')
        context = pa.default_serialization_context()

        if redis_canteen_value is None or not redis_canteen_value:
            todays_menu = self._get_menu(today)

            try:
                menu_df = pd.DataFrame(todays_menu)
                menu_df['mealName'] = menu_df.apply(
                    lambda x: [x['rows'][i]['item']['mealName'] for i in range(len(x['rows']))], axis=1)

                redis_value = context.serialize(menu_df).to_buffer().to_pybytes() if not menu_df.empty else ''
                r.set(f'canteen_menu_{today}', redis_value)
            except:
                menu_df = None
                todays_menu = ''
                r.set(f'canteen_menu_{today}', '')
        else:
            todays_menu = True
            menu_df = context.deserialize(redis_canteen_value)

        if todays_menu:
            message = ''

            if language == 'en':
                message += 'Today\'s menu in canteen: <br><br>'
            else:
                message += 'Dneska v menze mají: <br><br>'

            for _, row in menu_df.iterrows():
                message += row['mealKindName'] + '<br>'
                message += ' \u2022 ' + '<br> \u2022 '.join(row['mealName']) + '<br><br>'
        elif not todays_menu:
            if language == 'en':
                message = 'There is no canteen menu for today'
            else:
                message = 'Jídelníček na dneska není k dispozici'
        else:
            if language == 'en':
                message = 'Unfortunately we could not provide you with menu canteen at the moment'
            else:
                message = 'Momentálně ti bohužel nemůžeme ukázat jídelníček'


        dispatcher.utter_message(text=message)

        return []


class ActionGetConsultingHours(Action):
    def name(self) -> Text:
        return "action_get_consulting_hours"

    def _init_browser(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

        return browser

    def _authenticate_in_insis(self):
        """
        Not used currently
        """

        load_dotenv()

        insis_user = os.getenv('INSIS_USER')
        insis_password = os.getenv('INSIS_PASSWORD')

        self.browser.get('https://insis.vse.cz/auth/')

        input_field_xpaths = ["//input[@name='credential_0']", "//input[@name='credential_1']"]

        for xpath, credential in zip(input_field_xpaths, [insis_user, insis_password]):
            # Wait and click on location input field
            WebDriverWait(self.browser, 30).until(
                EC.element_to_be_clickable((By.XPATH, xpath))).click()

            inp = self.browser.find_element(By.XPATH, xpath)

            inp.send_keys(credential)

        login_button_xpath = "//input[@id='login-btn']"
        self.browser.find_element(By.XPATH, login_button_xpath).click()
        self.browser.refresh()

    def _get_data(self, professor):
        professor = professor.split(',')[0].replace('Ing.', '').replace('Ph.D.', '').replace('Bc.', '').replace('Doc.', '').strip()

        headers = {
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'cs-CZ,cs;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '466',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'insis.vse.cz',
            'Origin': 'https://insis.vse.cz',
            'Referer': 'https://insis.vse.cz/lide/?_m=104',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }

        data = {
            '_suggestKey': professor.lower(),
            'upresneni_default': '-;zam_pomery=1,2',
            '_suggestMaxItems': 25,
            'upresneni': 'zamestnanci',
            '_suggestHandler': 'lide',
            'lang': 'cz',
        }

        try:
            r = requests.post('https://insis.vse.cz/uissuggest.pl', data=data, headers=headers)
            people_found = r.json()['data']
        except:
            people_found = None

        return people_found

    def _get_consulting_hours(self, person_id):
        profile_url = f'https://insis.vse.cz/lide/clovek.pl?id={person_id}'

        self.browser = self._init_browser()
        self.browser.get(profile_url)

        try:
            consulting_hours_xpath = "//td[text() = 'Konzultační hodiny:' or text() = 'Consulting hours:']/parent::tr/td[2]"

            WebDriverWait(self.browser, 10).until(
                EC.visibility_of_element_located((By.XPATH, consulting_hours_xpath)))

            consulting_hours = self.browser.find_element(By.XPATH, consulting_hours_xpath).text.replace('\n', ' ')

            try:
                consulting_hours_link_xpath = consulting_hours_xpath + "//a"
                consulting_hours_link = self.browser.find_element(By.XPATH, consulting_hours_link_xpath).get_attribute('href')
            except:
                consulting_hours_link = ''

        except Exception:
            consulting_hours = None
            consulting_hours_link = ''
        finally:
            self.browser.close()

        return consulting_hours, consulting_hours_link

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        langcode = tracker.get_slot('langcode')

        name = tracker.get_slot('name')

        # Professor name can be passed as button payload using entity "name"
        if name is None:
            professor = tracker.get_slot('professor_name')
        else:
            professor = name

        people_found = self._get_data(professor)

        if not people_found:
            if langcode == 'en':
                message = f'Professor "{professor}" was not found in Insis'
            else:
                message = f'Učitel "{professor}" nebyl v Insisu nalezen'

            buttons_resp = [
                {"title": "Try again" if langcode == 'en' else "Zkusit znovu",
                 "payload": f'/action_get_consulting_hours{{"langcode": "{langcode}"}}'}
            ]
        elif len(people_found) > 1:
            # Output format for professor is: ['professor name', 'professor id', '', 'department']

            buttons_resp = [
                {"title": f'{x[0]} ({x[3]})',
                 "payload": f'/trigger_action_get_consulting_hours{{"name": "{x[0]}", "langcode": "{langcode}"}}'}
                for x in people_found
            ]

            if langcode == 'en':
                message = f'More than one professor with name "{professor}" found. Please choose one from list'
            else:
                message = f'Víc než 1 učitel "{professor}" nalezen. Vyběr si prosím ze seznamu'

        else:
            buttons_resp = None
            person = people_found[0]
            print(f'Found {person}')
            person_id = person[1]

            today = f'{datetime.datetime.now():%Y-%m-%d}'

            # First check if result from today does not already exist in Redis (to avoid unnecessary requests)
            # Note: chatbot_redis is name of Docker container from docker compose
            r = redis.Redis(host='localhost', port=6379, encoding="utf-8", decode_responses=True, db=0)

            redis_consulting_hours_value = r.get(f'consulting_hours_{person_id}_{today}')
            redis_consulting_hours_link_value = r.get(f'consulting_hours_link_{person_id}_{today}')

            if redis_consulting_hours_value is None:
                consulting_hours, consulting_hours_link = self._get_consulting_hours(person_id)

                r.set(f'consulting_hours_{person_id}_{today}', consulting_hours)
                r.set(f'consulting_hours_link_{person_id}_{today}', consulting_hours_link)
            else:
                consulting_hours = redis_consulting_hours_value
                consulting_hours_link = redis_consulting_hours_link_value

            if consulting_hours is not None:
                if langcode == 'en':
                    message = f'{professor} has the following consulting hours: <br><br>'
                else:
                    message = f'{professor} má následující konzultační hodiny: <br><br>'

                message += consulting_hours

                if consulting_hours_link:
                    if langcode == 'en':
                        message += f'<br><br> Link for booking: <a href="{consulting_hours_link}" target="_blank">book</a>'
                    else:
                        message += f'<br><br> Odkaz na rezervaci: <a href="{consulting_hours_link}" target="_blank">rezervovat</a>'
            else:
                if langcode == 'en':
                    message = f'Consulting hours of "{professor}" were not found'
                else:
                    message = f'Konzultační hodiny "{professor}" nebyly nalezeny'

        dispatcher.utter_message(text=message, buttons=buttons_resp)

        return [SlotSet("professor_name", None), SlotSet("name", None)]


def clean_name(name):
    return "".join([c for c in name if c.isalpha()])


class ValidateNameForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_professor_form"

    def validate_professor_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        # If the name is super short, it might be wrong.
        name = clean_name(slot_value)
        if len(name) < 5:
            dispatcher.utter_message(text="That must've been a typo.")
            return {"professor_name": None}

        return {"professor_name": name}


class ActionGetBuildingAddresses(Action):
    def name(self) -> Text:
        return "action_get_building_addresses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        language = tracker.get_slot('langcode')

        if language not in ['en', 'cs']:
            language = 'cs'

        building = next(tracker.get_latest_entity_values('uni_building'), None)

        study_programs_file = Path(Path(__file__).resolve().parent, 'sources', 'buildings_location.json')

        with study_programs_file.open(mode='r') as f:
            json_dict = json.load(f)

        default_message_en = """
                    VŠE is located in two locations in Prague.
                    <br>In <b>Žižkov</b> with the address: nám. W. Churchilla 1938/4, 130 67 Prague 3 - Žižkov. And in the <b>Jižní Město</b> area: Ekonomická 957, 148 00 Prague 4 - Kunratice
                    <br>In area Žižkov are located four buildings. <b>New building</b>, <b>Old building</b>, <b>Rajska building</b> and <b>Italska building</b>.
                    <br>\u2022 <b>Library</b> is located in Old building in Žižkov area.
                    <br>\u2022 Address of <b>dormitory Vltava</b>: Chemická 953, 148 00 Prague 4 - Jižní Město
                    <br>\u2022 Address of <b>dormitory Blanice</b>: Chemická 955, 148 00 Prague 4 - Jižní Město.
                    <br>\u2022 Address of <b>Rooseveltova dormitory</b>: Strojnická 1430/7, 170 00 Prague 7.
                    <br>\u2022 Address of <b>Eislerova dormitory</b>: V Zahrádkách 1953/67, 130 00 Prague 3.
                    <br>\u2022 Address of <b>Jarov II.</b>: Pod lipami 2603/43, 130 00 Prague 3.
                    <br>\u2022 Address of <b>Palachova dormitory</b>: Koněvova 93/198, 130 00 Prague 3.
                    <br>\u2022 Address of <b>Thalerova dormitory</b>: Jeseniova 1954/210, 130 00 Prague 3.
                """

        default_message_cs = """
                VŠE sídlí na dvou místech v Praze. 
                <br>Na <b>Žižkově</b> s adresou: nám. W. Churchilla 1938/4, 130 67 Praha 3 - Žižkov. A v areálu <b>Jižní Město</b>: Ekonomická 957, 148 00 Praha 4 - Kunratice.
                <br>V areálu Žižkov se nacházejí čtyři budovy. <b>Nová budova</b>, <b>Stará budova</b>, <b>Rajská budova</b> a <b>Italská budova</b>.
                <br>\u2022 <b>Knihovna</b> se nachází ve staré budově v areálu Žižkov.
                <br>\u2022 Adresa <b>koleje Vltava</b>: Chemická 953, 148 00 Praha 4 - Jižní Město.
                <br>\u2022 Adresa <b>koleje Blanice</b>: Chemická 955, 148 00 Praha 4 - Jižní Město.
                <br>\u2022 Adresa <b>Rooseveltové koleje</b>: Strojnická 1430/7, 170 00 Praha 7.
                <br>\u2022 Adresa <b>Eislerové koleje</b>: V Zahrádkách 1953/67, 130 00 Praha 3.
                <br>\u2022 Adresa <b>koleje Jarov II.</b>: Pod lipami 2603/43, 130 00 Praha 3.
                <br>\u2022 Adresa <b>Palachove koleje</b>: Koněvova 93/198, 130 00 Praha 3.
                <br>\u2022 Adresa <b>Thalerove koleje</b>: Jeseniova 1954/210, 130 00 Praha 3.
                """

        if building is None:
            message = default_message_en if language == 'en' else default_message_cs
        else:
            # Find building with the biggest probability using string difference
            similarity_list = dict(sorted({x: difflib.SequenceMatcher(None, x, building).ratio() * 100 for x in json_dict.keys()}.items(), key=lambda x: x[1], reverse=True))
            best_option_key, best_option_value = next(iter(similarity_list.items()))

            if best_option_value < 0.5:
                message = default_message_en if language == 'en' else default_message_cs
            else:
                message = f"The address is: {json_dict[best_option_key]}" if language == 'en' else f"Adresa je: {json_dict[best_option_key]}"

        dispatcher.utter_message(text=message)

        return []