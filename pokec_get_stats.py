# v0.1
import time

import config
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class User:
    def __init__(self, name, sex, age, city):
        self.name = name
        self.sex = sex
        self.age = age
        self.city = city


initial_room_link = "https://pokec-sklo.azet.sk/miestnost/" + config.room

# list of room links including locked rooms
room_list_all = []

# only locked room links
room_list_bad_links = []

# list of room links without locked rooms links
room_list = []

# each element of list is class with name, age, sex and city
user_list_one_room = []


def check_loaded_page(class_name, wait_time):
    # wait for the main page to load - check if Pomoc a podpora is loaded
    WebDriverWait(browser, wait_time).until(
        EC.presence_of_all_elements_located((By.XPATH, f"//*[@class='{class_name}']")))


def remove_locked_room_links(room_list_bad_links, room_list_all):
    # retrun lis which doesn't contain locked rooms links
    return [x for x in room_list_all if not any([x in room_list_bad_links])]

def find_rooms():
    print("*** Finding room links ***")
    # all room links has class sc-dtwoBo jtTzgD
    find_href_list_all = browser.find_elements(By.XPATH, '//*[@class="sc-dtwoBo jtTzgD"]')

    # extract each class instance from list
    # room_list contains links of rooms that are locked
    for my_href in find_href_list_all:
        # get attribute href from each class - we extract room links only
        room_list_all.append(my_href.get_attribute("href"))

    print("Number of all rooms, including those locked: ", len(room_list_all))

    # if sc-gsxnyZ eMyRzl is presented in class sc-dtwoBo jtTzgD, room is locked and we are redirected to main page
    # if we click link
    # if room is open sc-gsxnyZ eMyRzl is not pesented in c-dtwoBo jtTzgD and we can get into room
    find_href_list_bad = browser.find_elements(By.XPATH, '//div[@class="sc-gsxnyZ eMyRzl"]/ancestor::a[@class="sc-dtwoBo jtTzgD"]')

    for my_href2 in find_href_list_bad:
        #print(my_href2.get_attribute("href"))
        room_list_bad_links.append(my_href2.get_attribute("href"))

    print("Number of locked rooms: ", len(room_list_bad_links))

    room_List = remove_locked_room_links(room_list_bad_links, room_list_all)
    print("Number of non-locked room links: ", len(room_List), "\n")
    return room_List


def load_room(room_link):
    # load room page
    browser.get(room_link)

    # check if plus button in room column is presentes
    check_loaded_page("sc-nFpLZ jXWXLS", 20)

    # only few rooms have Rozumiem button, press it, if not presented just continue
    try:
        browser.find_element(By.XPATH, '//*[@class="Button-sc-1fngo4c-0 sc-hoXqvr bpnQvN kTgJcS"]').click()
    except NoSuchElementException:
        pass

    # checking if Odoslat button is available
    check_loaded_page("sc-BXqHe bwSTre", 20)


def find_actual_room_name():
    return browser.find_element(By.XPATH, '/html/body/main/div/div[1]/div[1]/div[1]/div[3]/div/div[2]/div[1]/span[1]').text


def find_users_rooms_by_pokec():
    # class not presented if there is no user in room, so we need to continue
    try:
        check_loaded_page("sc-jrAGrp sc-kEjbxe sc-iqHYGH lkoUPX ehwLew gvEvvK", 10)
        users_num_text = re.search("[\d]+", browser.find_element(By.XPATH, '//*[@class="sc-jrAGrp sc-kEjbxe sc-iqHYGH lkoUPX ehwLew gvEvvK"]').text)
        return int(users_num_text.group())
    except TimeoutException:
        users_num_text = 0
        pass
        return users_num_text

def compute_city_max_hits(city_list):
    cities_with_hits = {}
    for city in city_list:
        if city not in cities_with_hits:
            cities_with_hits.update({city: city_list.count(city)})

    city_name_max_hits =  max(cities_with_hits, key=cities_with_hits.get)
    city_max_hits = cities_with_hits.get(city_name_max_hits)
    print("\tNajviac ludi je z {}: {}".format(city_name_max_hits, city_max_hits))
    return city_name_max_hits, city_max_hits


def compute_results(user_list_one_room, count_dash, suma_age):
    woman_count = man_count = city_hits = 0
    city_list = []
    cities_with_hits_dict = {}
    # go through attributes of list
    for attribute in user_list_one_room:
        # compute sum for age computing
        if attribute.age == "-":
            count_dash+=1
        else:
            # if user has no age shown char "-" is presented, so we need to skip it
            suma_age = suma_age + int(attribute.age)

        # woman and men count
        if attribute.sex == "Ž":
            woman_count+=1
        elif attribute.sex == "M":
            man_count+=1

        # add city to city list
        city_list.append(attribute.city)

    city_name_max_hits, city_max_hits = compute_city_max_hits(city_list)


    woman_percentage = round(woman_count / number_users * 100, 2)
    man_percentage = round(man_count / number_users * 100,2)

    # compute average age
    if number_users - count_dash != 0:                    # skip condition if there is only one user in room and has not age visible
        avg_age = round((suma_age / (number_users - count_dash)),1)     # 1 digit after comma
    else:
        avg_age = "nie je mozne urcit"

    return avg_age, woman_count, man_count, woman_percentage, man_percentage, city_name_max_hits, city_max_hits

### BODY ###

options = webdriver.ChromeOptions()

# maximallie Chrome window
options.add_argument("--start-maximized")

s = Service(config.chrome_driver_path)
browser = webdriver.Chrome(service=s, options= options)

# load main web page
browser.get("https://pokec.azet.sk")

# accept privacy statement
browser.find_element(By.CLASS_NAME, "fc-button-label").click()

# enter username + pass
browser.find_element(By.XPATH, '//*[@class="Input-sc-1vv8hqf-0 HeaderLoginFormstyles__StyledInput-sc-1tqermr-6 iAjQwL gCOXow"]').send_keys(config.username)
browser.find_element(By.XPATH, '//*[@class="Input-sc-1vv8hqf-0 HeaderLoginFormstyles__PasswordInput-sc-1tqermr-7 iAjQwL hEuONx"]').send_keys(config.password)

# click submit button
browser.find_element(By.XPATH, '//*[@class="Button-sc-1fngo4c-0 HeaderLoginFormstyles__LoginButton-sc-1tqermr-4 ddPToY bZDNfj"]').click()
check_loaded_page("wI9", 20)

load_room(initial_room_link)

# get room list
room_list = find_rooms()


for room_link in room_list:    # go from room to room
    number_users = suma_age = avg_age = count_dash = 0
    load_room(room_link)

    room_name = find_actual_room_name()
    print("*** Room name is: ", room_name, " ***")
    print("\tRoom link is: ", room_link)
    # frame next to Odoslat button where we write text

    users_count_by_pokec = find_users_rooms_by_pokec()
    print("\tNumber of users in room: {} counted by pokec: {}".format(room_name, users_count_by_pokec))

    # need to wait otherwise users are not loaded
    if users_count_by_pokec < 200:
        browser.implicitly_wait(5)
    elif 200 < users_count_by_pokec < 600:
        browser.implicitly_wait(10)
    else:
        browser.implicitly_wait(15)

    # list contains multiple instance of same class, each class is use
    user_class_list = browser.find_elements(By.XPATH, '//*[@class="sc-bBXqnf bGwFiF"]')

    # extract each user class from list
    for user_class in user_class_list:
        # remove Enter between name an other, result = e.g. BaronVyprasil / M / 42 / Prievidza
        user_all_attributes = (user_class.text.replace("\n", " / "))

        # remove spaces
        user_all_attributes =  user_all_attributes.replace(" ", "")

        # split name, gender, age and city to variables, they are parameters of class User
        a,b,c,d = user_all_attributes.split("/")
        obj = User(a,b,c,d)

        # assign object to list
        user_list_one_room.append(obj)

        number_users += 1

    avg_age, woman_count,  man_count, woman_percentage, man_percentage, city_name_max_hits, city_max_hits = compute_results(user_list_one_room, count_dash, suma_age)

    print("\tV miestnosti: {} je: {} osob, z toho: zeny: {} - {}%, muzi: {} - {}%, priemerny vek osob: {}, najviac ludi je z: {} - {}\n".
          format(room_name,number_users,woman_count,woman_percentage,man_count,man_percentage,avg_age,city_name_max_hits, city_max_hits))

    message_glass = f"V miestnosti: {room_name} - {number_users} osob(y), z toho: zeny: {woman_count} - {woman_percentage}%, muzi: {man_count} - {man_percentage}%, priemerny vek pouzivatelov: {avg_age},  najviac ludi je z: {city_name_max_hits} - {city_max_hits}"

    # wait until frame for entering message is loaded
    check_loaded_page('sc-gUUzQN gUbXEK', 20)

    # send message to glass
    browser.find_element(By.XPATH, '/html/body/main/div/div[1]/div[1]/div[2]/div[2]/div[2]/div/div[2]/div[1]/div/div[2]/div/div/div/div/span/br').send_keys(message_glass)

    # click Odoslat button
    browser.find_element(By.XPATH, '//*[@class="sc-BXqHe bwSTre"]').click()

    # user list must be empty for new room
    user_list_one_room = []
