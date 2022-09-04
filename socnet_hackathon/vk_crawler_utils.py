import time
import os
import requests

from PIL import Image
from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BROWSER = None

def vk_login(email, pwd):
    """Logins into specified VK account"""
    global BROWSER
    if BROWSER is None:
        BROWSER = webdriver.Chrome(ChromeDriverManager().install())

    BROWSER.get('https://vk.com/')
    email_field = WebDriverWait(BROWSER, 10).until(EC.presence_of_element_located((By.ID, "index_email")))
    email_field.send_keys(email)

    BROWSER.find_element(By.CLASS_NAME, 'VkIdForm__signInButton').click()
    pwd_field = WebDriverWait(BROWSER, 10).until(EC.presence_of_element_located((By.NAME, "password")))
    pwd_field.send_keys('Password123')
    BROWSER.find_element(By.CLASS_NAME, 'vkuiButton__in').click()

def get_profile_name(id_):
    """Returns the name and info associated with a VK account."""
    vk_url = f'https://vk.com/id{id_}'
    print(vk_url)
    time.sleep(1)
    BROWSER.get(vk_url)
    page_name = WebDriverWait(BROWSER, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "page_name")))
    name = page_name.text
    return {"vkId": id_, "vk_link": f"https://vk.com/id{id_}", "name": name}


SCROLL_PAUSE_TIME = 0.5
def scrape_friends(id_):
    """Scrapes the friends associated with a particular friend id. Note the this involves
    the automated scrolling of downward of the browser-window to grab all friends. This
    scrolling will not happen if a screensaver is running."""
    url = f'https://vk.com/friends?id={id_}&section=all'
    BROWSER.get(url)
    friends = load_friends_info(BeautifulSoup(BROWSER.page_source, features="lxml"))
    if not friends:
        return []

    _scroll_down()
    if len(friends) > 5:
        time.sleep(0.5)
        _scroll_down()

    html = BROWSER.page_source
    soup = BeautifulSoup(html, features="lxml")
    return load_friends_info(soup)

def load_friends_info(soup):
    """Loads friend divs from Beautiful soup."""
    class_name = "friends_user_row friends_user_row--fullRow"
    friend_divs =  soup.find_all('div', attrs={"class": class_name})
    friends = [_get_friend_info(div) for div in friend_divs]
    return [friend for friend in friends if friend]

def _get_friend_info(div):
    """Gets the information for an individual friend."""
    id_ = _get_friend_id(div)
    if not id_:
        return {}

    img = div.find('img')
    if not img:
        return {}

    name = img.get('alt')
    if not name or name == 'DELETED':
        return {}

    src_url = img['src']
    if not src_url.startswith('https:'):
        return {}

    return {"vkId": id_,
            "vk_link": f"https://vk.com/id{id_}",
            "name": name,
            "img": src_url}

def _get_friend_id(div):
    friend_id = div.get('id', '')
    if 'friends_user_row' in friend_id:
        return friend_id.split('friends_user_row')[-1].strip()
    else:
         return ''

def _scroll_down():
    """Keeps scrolling the browser window downward to load more friends."""
    last_height = BROWSER.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        BROWSER.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = BROWSER.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_orc_images(vk_id, img_path):
    """Downloads all images associated with a vk id. Returns the stored filenames of these images."""
    fnames = []
    url = f'https://vk.com/id{vk_id}'
    img_profile, img_list = get_orc_img_urls(url)
    if img_profile:
        fnames.append(download_prof_pic(vk_id, img_profile, path=img_path))

    fnames.extend(download_orc_imgs(vk_id, img_list, path=img_path))
    return fnames

def get_orc_img_urls(vk_url, fname_prefix='vk_profile_'):
    """Downloads all image photos accessible from main VK page."""
    image_files = []
    soup = load_vk_soup(vk_url)

    imgs = [a.get('href')
        for a in soup.find_all('a', attrs={"id":"profile_photo_link"})]

    imgs = ['https://vk.com' + img + '?rev=1' for img in imgs if img]
    img_a = imgs[0] if imgs else ''
    imgs = [a.get('src')
        for a in soup.find_all('img', attrs={"class":"page_avatar_img"})]
    img_b = imgs[0] if imgs else ''
    imgs_c = ['https://vk.com' + a.get('href')
              for a in soup.find_all('a', attrs={"class":"page_square_photo"})]

    if img_b:
        return img_b, imgs_c
    return '', [img_a] + imgs_c if img_a else imgs_c

def load_vk_soup(url):
    """Loads url html in BS"""
    BROWSER.get(url)
    html = BROWSER.page_source
    soup = BeautifulSoup(html, features="lxml")
    return soup


def download_prof_pic(id_, pimage_url, path='images'):
    """Downloads the profile picture directly and writes to disk."""
    img_suffix = f'vk_pf'
    fname_prefix = f"{path}/{id_}_{img_suffix}"
    suffix = '_0.jpg'
    fname = fname_prefix + suffix
    img_data = requests.get(pimage_url).content
    with open(fname, 'wb') as handler:
        handler.write(img_data)
    handler.close()

    return fname

def download_orc_imgs(id_, image_list, path='images'):
    """Downloads all image photos accessible from main VK page using screenshots, since these images
    are trickier to download directly."""
    fnames = []
    for i, url  in enumerate(image_list):
        img_suffix = f'vk_rest'
        fname_prefix = f"{path}/{id_}_{img_suffix}"
        suffix = f'_{i}.jpg'
        fname = fname_prefix + suffix
        try:
            _save_orc_pic(url, fname)
        except:
            continue

        fnames.append(fname)

    return fnames


def _save_orc_pic(url, fname):
    """Saves screenshot to temporary image"""
    BROWSER.get(url)
    time.sleep(0.5)
    # Takes a screenshot.
    BROWSER.save_screenshot("screenshot.png")
    im = Image.open("screenshot.png").convert('RGB').save(fname,"JPEG")
