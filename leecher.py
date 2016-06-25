import re
import time
from datetime import datetime
import os,os.path
import logging

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


from bs4 import BeautifulSoup
import configparser
import requests
import zipfile

import downloader
import unzipper



logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='leecher.log',
                    filemode='w')

logging.info('123456')

s = requests.Session()
website = 'http://www.zimuzu.tv'
headers = {'Connection': 'keep-alive',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Origin': 'http://www.zimuzu.tv',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.22 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'http://www.zimuzu.tv/user/login',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8'
           }

config = configparser.ConfigParser()
config.read('leecher.config',encoding='utf-8')

def login():
    user = config.get('user','id')
    password = config.get('user','password')
    logging.info("Login as " + user)
    
    url = website + '/User/Login/ajaxLogin'
    payload = 'account=%s&password=%s&from=loginpage&remember=0&url_back='%(user, password)
    r = s.post(url, headers=headers, data=payload)

    logging.info("Login cookie " + r.headers['set-cookie'])

def send_mail(sub,content,sub_zip):


    subscribers = config.get('email','subscriber')
    logging.info("Send mails to " + subscribers)
    if subscribers:
        to_list = [str.strip() for str in subscribers.split(',')]
    else:
        return False
    
    mail_host = config.get('email','host')
    mail_user = config.get('email','user')
    mail_pass = config.get('email','password')
    mail_postfix = config.get('email','postfix')
    
    attach_zip = open(sub_zip,'rb')
    attachment = MIMEApplication(attach_zip.read(),Name='sub.zip')
    attachment.add_header('Content-Disposition', 'attachment', filename='sub.zip')
    me="zimuzu"+"<"+mail_user + "@" + mail_postfix + ">"
    #msg = MIMEText(content,_subtype='plain',_charset='utf-8')
    msg = MIMEMultipart()
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    msg.attach(MIMEText(content))
    msg.attach(attachment)
    try:
        server = smtplib.SMTP()
        server.connect(mail_host)
        server.login(mail_user,mail_pass)
        server.sendmail(me, to_list, msg.as_string())
        server.close()
        return True
    except Exception as e:
        logging.info(str(e))
        return False

url_sub_template = website + "/search?keyword=%s&type=subtitle"
def inquiry_subtitle(since = None, page = 0):

    resource_list = [str.strip() for str in config.get('resource','name').split(',')]
    logging.info("Resource list: " + str(resource_list))

    since = config.get('history','since')
    format = '%Y-%m-%d %H:%M'
    if since:
        since_time = datetime.strptime(since, format )
    else:
        since_time = datetime.min

    logging.info("Start searching subtitle download link since " + since_time.strftime(format))

    result = {}
    for name in resource_list:
        result.update(inquiry_subtitle_on_resource(name,since_time))

    logging.info("Update the history-since time in config file.")
    config.set('history','since',datetime.now().strftime(format))
    config.write(open('leecher.config', 'w', encoding='utf-8'))

    return result

url_sub_template = website + "/search?keyword=%s&type=subtitle&page=%d"
def inquiry_subtitle_on_resource(name, since_time, page = 1):

    result = {}
    logging.info("Searching for: " + name)
    url = url_sub_template % (name,page)
    r = s.get(url,headers=headers)
    html_doc = r.content
    soup = BeautifulSoup(html_doc)
    
    for tag in soup.find_all('div',attrs={'class':'clearfix search-item'}):
        a_tag = tag.find('a')
        sub_url = a_tag['href']

        value = pickup_subtitle_link(sub_url, since_time)
        if value:
            resource_id, download_link = value
            if resource_id:
                if resource_id in result:
                    result[resource_id].append(download_link)
                else:
                    result[resource_id] = [download_link]
        else:
            logging.info("No more new subtitles, stop the searching")
            return result
    logging.info("Check next page")
    page_tag = soup.find('a', class_='cur')
    if page_tag and page_tag.find_next_sibling('a'): #page_tag not null means there are more than 1 pages; next sibling not null means this is not the last page
        logging.info("inquiry the next page %d" % (page + 1))
        next_result = inquiry_subtitle_on_resource(resource_name, since_time, page+1)
        for resource_id in next_result:
            if resource_id in result:
                result[resource_id] = result[resource_id] + next_result[resource_id]
            else:
                result[resource_id] = next_result[resource_id]
    else:
        logging.info('No next page.')
    
    return result

def pickup_subtitle_link(sub_url, since_time):
    if not sub_url.startswith('http'):
        sub_url = website + sub_url
    r = s.get(sub_url,headers=headers)
    sub_soup = BeautifulSoup(r.content)
    logging.info("Find subtitle download link: " + sub_url)
    ul_tag = sub_soup.find('ul',attrs={'class':'subtitle-info'})
    for li in ul_tag.find_all('li'):
        if('【發布】' in li.string):
            pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})')
            match = pattern.search(li.string)
            if(match):
                last_update = match.groups()[0]
                logging.info("Subtitle was updated at " + last_update)
                last_update_time = datetime.strptime(last_update, '%Y-%m-%d %H:%M' )
                if last_update_time < since_time:
                    logging.info("It is old than we need, return.")
                    return None
                else:
                    break
    download_tag = sub_soup.find('div',attrs={'class':'subtitle-links tc'})
    download_link = download_tag.h3.a['href']
    resource_tag = sub_soup.find('div',attrs={'class':'box subtitle-ralate'})
    if resource_tag:
        resource_link = resource_tag.find('a',href=True)
        resource_id = resource_link['href'].split('/')[-1]
        logging.info('Resource id found:' + resource_id)
        return resource_id, download_link
    else:
        return None,download_link


def download_subtitle(resource_dict):
    logging.info("Download and unzip subtitle zip file")    
    result = {} #map: resource id -> resource(name) name list
    output_dir = config.get('resource','output_dir')
    target_dir = datetime.now().strftime('%Y%m%d-%H%M%S')
    target_location = os.path.join(output_dir, target_dir)

    lang_list = [str.strip() for str in config.get('resource','sub_lang').split(',')]
    logging.info("Language: " + str(lang_list))
    
    for id in resource_dict:
        sub_list = resource_dict[id]
        for link in sub_list:
            logging.info("Downloading " + link)
            file = downloader.download(link)
            #logging.info(file)
            resource_name_set = unzipper.extract(file, target_location, lang_list)
            if id in result:
                result[id] = result[id].union(resource_name_set)
            else:
                result[id] = resource_name_set

    logging.info("Clean temp files.")
    downloader.clean()        
    return target_location, result            

#find related ed2k or magnet links for the related subtitle
def collect_resource_download_link(resource_item_map):

    logging.info("Collect resource download link for: " + str(resource_item_map))

    item_2_dlink = {}
    for id in resource_item_map:
        logging.info("resource id: " + id)
        item_list = resource_item_map[id]

        url = website + '/resource/list/%s' % id
        capture_resource_download_link(url,item_list,item_2_dlink)
    return item_2_dlink


def capture_resource_download_link(url, item_list,item_2_dlink):
    logging.info("Coolect download link from " + url)
    r = s.get(url,headers=headers)
    html_doc = r.content
    soup = BeautifulSoup(html_doc)

    for item in item_list:
        item = item.replace('.','\.')
        logging.info("Looking for " + item)
        
        a_title = soup.find('a',title=re.compile(item))
        if a_title:
            li_clearfix = a_title.find_parent('li', class_='clearfix')
            a_link = li_clearfix.find('a',href=True)

            download_link = a_link['href']
            logging.info("Link %s found." % download_link)
            item_2_dlink[item] = download_link


def generate_notification(item_2_dlink, subtitle_location):
    logging.info(item_2_dlink)

    if not item_2_dlink:
        return
    
    content = ""
    for item_name in item_2_dlink:
        
        content = "%s name: %s\n download link: \n%s\n" %(content,item_name, item_2_dlink[item_name])

    content = content + "\nAll download link:\n" + "\n".join(item_2_dlink.values())

    sub_zip = zipfile.ZipFile(os.path.join(subtitle_location,'sub.zip'),'w')
    for sub in os.listdir(subtitle_location):
        #zip the received subtitle files
        if sub.endswith('.ass') or sub.endswith('.srt'):
            sub_zip.write(os.path.join(subtitle_location,sub),sub)

    sub_zip.close()
    sub_zip_file = os.path.join(subtitle_location, 'sub.zip')
    
    with open(os.path.join(subtitle_location,'link.txt'),'w') as file:
        file.write(content)
    logging.info(content)
    send_mail("New subtitles downloaded!",content,sub_zip_file)
    
    
    

def burn():
    
    login()
    
    #inquiry latest subtitles
    result = inquiry_subtitle()

    #download and unzip subtitles
    subtitle_location, resource_name_map = download_subtitle(result)
    
    item_2_dlink = collect_resource_download_link(resource_name_map)

    generate_notification(item_2_dlink, subtitle_location)
        
                
        
        #unzip subtitle


            
 
    

burn()

    
    
