import requests
from bs4 import BeautifulSoup
import json

subjects_set = {'obzestvoznanie', 'russkiy', 'informatika', 'biologiya', 'geografiya',
                'ximiya', 'fizika', 'literatura', 'history', 'matematika', 'lang'}


def retrive_id_spec():
    """
    retrieves mapping specialization_id-specialization_name from
    'https://moeobrazovanie.ru/specialities_vuz/'
    :return: nothing, id-name is stored in 'id_speciality.json', name-id in 'speciality_id.json'
    """
    spec_id_dict = {}
    id_spec_dict = {}

    specs_url = 'https://moeobrazovanie.ru/specialities_vuz/'
    r = requests.get(specs_url)
    text = r.text
    soup = BeautifulSoup(text, 'html.parser')
    # going through all specializations from the webpage
    for spec in soup.find_all("a"):
        if spec.get('class') == ['spec_articles_list_spec_link']:
            link = spec.get('href').split('/')[-1]
            new_url = specs_url + link
            r = requests.get(new_url)
            text = r.text
            soup_new = BeautifulSoup(text, 'html.parser')
            name = soup_new.find_all("h1")[1].get_text()
            for td in soup_new.find_all("td"):
                if td.get_text().startswith("Код") \
                        and not td.get('class') == ['specHelmImg']:
                    id = str(list(td.children)[0]).split(" ")[-1]
                    break
            spec_id_dict[name] = [id]
            id_spec_dict[id] = name

    with open('id_speciality.json', 'w', encoding="utf-8") as fp:
        json.dump(id_spec_dict, fp, ensure_ascii=False, indent=4, separators=(',', ': '))
    with open('speciality_id.json', 'w', encoding="utf-8") as fp:
        json.dump(spec_id_dict, fp, ensure_ascii=False, indent=4, separators=(',', ': '))


def retrieve_exam_threshold(id_spec_dict):
    """
    retrieves universities' specializations with their Russian State Exam threshold and
    set of subjects that needs to be passed
    :param id_spec_dict: dictionary, id_of_specialization:name_of_specialization
    :return: nothing, 'universities.csv' is created with following structure:
    "University, Spec_ID, Spec_Name, Subjects, Threshold, Subjects_Count"
    """
    base_url = 'http://postyplenie.ru/calculator.php?Vuz=all&"'
    middle_url = ""
    end_url = 'Submit.x=60&Submit.y=23'

    list_subjects = []
    # setting all exams to be passed with 100 points to retrieve all possible specializations
    for item in subjects_set:
        middle_url += item + "=100&"
    url = base_url + middle_url + end_url
    url = url.replace('"', '')

    r = requests.get(url)
    text = r.text

    universities = dict()
    list_universities = []
    list_grades = []
    list_ids = []
    count_subjects = []
    soup = BeautifulSoup(text, 'html.parser')

    for td in soup.find_all('td'):
        if td.get('class') == ['light_gray_blue']:  # university name
            list_universities.append(td.get_text())
        if td.get('style') == 'white-space:nowrap;':  # exam threshold
            list_grades.append(td.get_text())
        if td.get('class') == ['light_gray_back', 'gray_border_right']:  # specialization id
            list_ids.append(td.get_text().strip())
        if td.find('div') != None and \
                td.find('div').get("class") == ['small_text', 'gray_text']:  # list of subjects
            subjects = td.find('div').get_text()
            list_subjects.append(subjects)
            count_subjects.append(len(str(subjects).split(",")))

    for i in range(len(list_universities)):
        univ_name = list_universities[i]
        if univ_name in universities:
            universities[univ_name].append((list_ids[i], id_spec_dict[list_ids[i]],
                                            list_subjects[i], list_grades[i],
                                            count_subjects[i]))
        else:
            universities[univ_name] = [(list_ids[i], id_spec_dict[list_ids[i]],
                                        list_subjects[i], list_grades[i],
                                        count_subjects[i])]

    with open('universities.csv', 'w', encoding='utf-8') as f:
        f.write("University, Spec_ID, Spec_Name, Subjects, Threshold, Subjects_Count\n")
        for key in universities:
            for i in range(len(universities[key])):
                result = '"%s",' % key
                for item in universities[key][i]:
                    result += '"%s",' % item
                result = result[:-1] + "\n"
                f.write(result)


def retrieve_spec_info(spec_id_dict):
    """
    retrieve description and perspectives of specializations
    :param spec_id_dict: dictionary, name_of_specialization:id_of_specialization
    :return: nothing, 'specialities.csv' is created with following structure:
    "Specialization, Description, Perspectives"
    """
    new_url = 'https://www.ucheba.ru/for-abiturients/speciality'
    r = requests.get(new_url)
    text = r.text
    soup = BeautifulSoup(text, 'html.parser')

    # going through all specializations on the webpage
    for div in soup.find_all("div"):
        if div.get('class') == ['col-sm-4', 'fs-large', 'mb-15']:
            speciality_id = str(div.find('a').get('href')).split('/')[-1]
            speciality_name = div.get_text().replace("\n", "")

            url_speciality = new_url + "/" + str(speciality_id)
            r = requests.get(url_speciality)
            text = r.text
            soup_speciality = BeautifulSoup(text, 'html.parser')

            for div_spec in soup_speciality.find_all("div"):
                if div_spec.get('class') == ['mb-section']:
                    for h2 in div_spec.find_all('h2'):
                        if h2.get_text() == 'Кем работать':
                            spec_descr = div_spec.get_text().replace("\n", ""). \
                                replace("Кем работать", "").replace("\t", "")
                        if h2.get_text() == 'Перспективы':
                            spec_perspecs = div_spec.get_text().replace("\n", ""). \
                                replace("Перспективы", "").replace("\t", "")
            try:
                spec_id_dict[speciality_name].append(spec_descr)
                spec_id_dict[speciality_name].append(spec_perspecs)
            except KeyError:
                continue

    with open('specialities.csv', 'w', encoding='utf-8') as f:
        f.write("Specialization, Description, Perspectives")
        for key in spec_id_dict.keys():
            try:
                f.write('"%s",%s,"%s","%s"\n' % (key, spec_id_dict[key][0],
                                                 spec_id_dict[key][1], spec_id_dict[key][2]))
            except IndexError:
                f.write('"%s",%s,,\n' % (key, spec_id_dict[key][0]))


js = open('id_speciality.json', encoding='utf-8').read()
id_spec_dict = json.loads(js)
js = open('speciality_id.json', encoding='utf-8').read()
spec_id_dict = json.loads(js)
