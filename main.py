import os
import re
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
import concurrent.futures
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput

exclude_sizes_file = "exclude_sizes.txt"

class MyImageApp(App):
    def build(self):
        self.title = 'My Image Viewer'
        layout = BoxLayout(orientation='vertical')

        # Créez un menu déroulant pour choisir entre les deux codes
        dropdown = DropDown()
        button_run_instant_code = Button(text='Instant Code', size_hint_y=None, height=44)
        button_run_test_code = Button(text='Test Code', size_hint_y=None, height=44)

        button_run_instant_code.bind(on_release=lambda btn: self.run_code('instant'))
        button_run_test_code.bind(on_release=lambda btn: self.run_code('test'))

        dropdown.add_widget(button_run_instant_code)
        dropdown.add_widget(button_run_test_code)

        main_button = Button(text='Choisir un code', size_hint=(None, None))
        main_button.bind(on_release=dropdown.open)
        dropdown.bind(on_select=lambda instance, x: setattr(main_button, 'text', x))

        layout.add_widget(main_button)

        self.status_label = Label(text='Cliquez sur le bouton pour charger les images')
        layout.add_widget(self.status_label)
        
        self.load_button = Button(text='Charger les images', on_release=self.load_images)
        layout.add_widget(self.load_button)

        return layout

    def open_images_in_chrome(self, image_urls):
        for image_url in image_urls:
            webbrowser.open(image_url)

    def run_instant_code(self):
        year = datetime.now().year
        month = datetime.now().strftime("%m")
        url = "https://instant-sport.com/wp-content/uploads/"
        base_url = f"{url}{year}/{month}/"
        self.status_label.text = f"On va chercher toutes les images de l'année à l'adresse {base_url}"
        response = requests.get(base_url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        current_date = datetime.now().strftime('%Y-%m-%d')
        yesterday_date = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")

        if os.path.exists(exclude_sizes_file):
            with open(exclude_sizes_file, "r") as f:
                exclude_sizes = f.read().splitlines()
        else:
            exclude_sizes = []

        images_today = []
        images_yesterday = []
        a_tags = soup.find_all('a')

        for a_tag in a_tags:
            img_relative_url = a_tag['href']
            img_full_url = urljoin(base_url, img_relative_url)
            pattern = r'-\d+x\d+'
            resultats = re.findall(pattern, img_relative_url)

            if current_date in img_full_url and not any(size in img_relative_url for size in exclude_sizes):
                images_today.append(img_full_url)
            elif yesterday_date in img_full_url and not any(size in img_relative_url for size in exclude_sizes):
                images_yesterday.append(img_full_url)
            else:
                for size in resultats:
                    if size not in exclude_sizes:
                        exclude_sizes.append(size)

        with open(exclude_sizes_file, "w") as f:
            f.write("\n".join(exclude_sizes))

        if len(images_today) == 0:
            self.status_label.text = "Il n'y a pas d'images en ce moment aujourd'hui mais hier il y avait : "
            for i in images_yesterday:
                self.status_label.text += "\n" + i
        else:
            self.status_label.text = "Images d'aujourd'hui :"
            for i in images_today:
                self.status_label.text += "\n" + i
            self.open_images_in_chrome(images_today)

    

    

    def run_test_code(self):
        base_url = "https://www.wesleycoaching.com/wp-content/uploads/"
        cpt_final = input("Combien d'image Wesley a dit ? : ")
        year = datetime.now().year
        month = datetime.now().strftime("%m")
        day = datetime.now().strftime("%d")

        print(f"On va chercher toutes les images de l'année à l'adresse {base_url}{year}/{month}/")

        range_of_images_debut = int(input("Entrez le numéro de la première image : "))
        range_of_images_fin = int(input("jusqu'au numéro de la dernière image : "))
        image_numbers = range(range_of_images_debut, range_of_images_fin + 1)
        total_images = len(image_numbers)
        images_found = 0

        progress_bar_length = 50
        start_time = datetime.now()

        today = datetime.now().date()
        dateTodayString = today.strftime("%Y-%m-%d")
        yesterday = today - timedelta(days=1)
        dateYesterdayString = yesterday.strftime("%Y-%m-%d")

        print("today : " + str(today) + " yesterday " + str(yesterday))

        images_today = []
        images_yesterday = []

        def update_progress(progress_percentage):
            progress_bar = '-' * int(progress_percentage / 100 * progress_bar_length)
            sys.stdout.write(f"\r[{progress_bar:{progress_bar_length}}] {progress_percentage:.2f}%")
            sys.stdout.flush()

        print("Progression: ", end="")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for img_number in image_numbers:
                futures.append(executor.submit(process_image, img_number, year, month, dateTodayString, dateYesterdayString, cpt_final, images_today, images_yesterday))

            for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                if isnombreimagesuffisante(images_today, cpt_final):
                    update_progress(100)
                    break
                progress_percentage = (idx / total_images) * 100
                update_progress(progress_percentage)

        elapsed_time = (datetime.now() - start_time).seconds
        images_per_second = images_found / elapsed_time if elapsed_time > 0 else 0
        remaining_images = total_images - images_found
        estimated_remaining_time_seconds = remaining_images / images_per_second if images_per_second > 0 else 0
        estimated_remaining_time_formatted = format_time(estimated_remaining_time_seconds)

        update_progress(100)
        print("\n\n")

        print("\nProgression : 100.00%")
        print("\n\n")

        if len(images_today) > 0:
            print("Photos prises aujourd'hui:")
            for image_url in images_today:
                print(image_url)
        else:
            print("Aucune photo prise aujourd'hui.")

        if len(images_yesterday) > 0:
            print("\nPhotos prises hier:")
            for image_url in images_yesterday:
                print(image_url)
        else:
            print("Aucune photo prise hier.")
        choice = input("Voulez-vous ouvrir les images dans Chrome (C) ou les télécharger (T)? ").lower()

        if choice == "c":
            if len(images_today) != 0:
                self.open_images_in_chrome(images_today)


def check_image_url(image_url):
    response = requests.head(image_url)
    return response.status_code == 200

def get_image_modified_date(image_url):
    response = requests.head(image_url)
    if response.status_code == 200:
        modified_date = response.headers.get('Last-Modified')
        return modified_date
    return None

def convertion_string_en_date_simple_format(date_string):
    date_object = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')
    formatted_date = date_object.strftime('%Y-%m-%d')
    return formatted_date

def isnombreimagesuffisante(images_today, cpt_final):
    if int(cpt_final) == len(images_today):
        print("Image trouvée pour aujourd'hui. Arrêt de la recherche.")
        return True
    return False



def process_image(img_number, year, month, dateTodayString, dateYesterdayString, cpt_final, images_today, images_yesterday):
    base_url = "https://www.wesleycoaching.com/wp-content/uploads/"
    image_url = f"{base_url}{year}/{month}/IMG_{img_number:04d}.jpg"
    if check_image_url(image_url):
        modified_date = convertion_string_en_date_simple_format(get_image_modified_date(image_url))
        if modified_date == dateTodayString:
            images_today.append(image_url)
            print(f"Image {image_url} existe.")
            isnombreimagesuffisante(images_today, cpt_final)
        elif modified_date == dateYesterdayString:
            images_yesterday.append(image_url)

def isnombreimagesuffisante(images_today, cpt_final):
    if int(cpt_final) == len(images_today):
        print("Image trouvée pour aujourd'hui. Arrêt de la recherche.")
        return True
    return False

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

if __name__ == '__main__':
    MyImageApp().run()
