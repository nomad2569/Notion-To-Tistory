from bs4 import BeautifulSoup
import base64
import re
import pprint
import requests
import os, shutil
import zipfile

config = {
    "ACCESS_TOKEN" :"dd4720376e6a5d1790b5e1732dcc87c1_c2399f0fbc3c7e1682a4e7b0f518277d",
    "BLOG_NAME" : "private-k",
    "REMOVE_AFTER_UPLOAD" : False,
    "upload_path" : "/Users/minkyukim/Desktop/Project/Notion To Tistory/upload",
    
    "CODE_AS_PYTHON" : False,
    "CODE_AS_TYPESCRIPT" : True
}
os.chdir(config["upload_path"])
path_list = os.listdir()
if '.DS_Store' in path_list:
    path_list.remove(".DS_Store")

html_list, png_list = [], []

for _ in path_list:
    png_list.append({})

for idx, path in enumerate(path_list):
    file_name_list = os.listdir(path)
    if '.DS_Store' in file_name_list:
        file_name_list.remove('.DS_Store') 

    for file_name in file_name_list:
        if '.html' in file_name:
            html_list.append(open(f"{path}/{file_name}", 'rt', encoding='utf-8').read())

for html_idx, html_value in enumerate(html_list):
    # html 로드하기
    soup = BeautifulSoup(f"upload/{html_value}", 'html.parser')

    # 기존 head 태그(meta, title, style) 제거
    soup.find('meta').extract()
    soup.find('title').extract()
    soup.find('style').extract()

    # 본문 내용 가져오기
    article = soup.find('article')
    header = soup.find('header')

    # class 명 추가(Notion_P라는 클래스를 추가하여 css 관리 위함)
    article['class'].append('Notion_P')

    # code 를 python 으로 하이라이트 할 것이라면,
    if config["CODE_AS_PYTHON"] :
        code_list = soup.select('pre')
        for code in code_list:
            code['class'].append('hljs language-python')
    elif config["CODE_AS_TYPESCRIPT"]:
        code_list = soup.select('pre')
        for code in code_list:
            code['class'].append('hljs language-typescript')

    # details 닫기 처리 해두기
    details = article.find_all('details')
    for detail in details:
        del detail["open"]
    
    # 상태, 카테고리, 태그 가져오기
    columns = article.find_all('tr')
    tags = []
    CATEGORY = ""
    for col in columns:
        if col.find('th') is None :
            continue
        col_name = col.find('th').text
        if col_name=='Status':
            status = col.find('td').text
        elif col_name=='Category':
            CATEGORY = col.find('td').text
        elif col_name=='Tag':
            tags = col.find('td')
            tags = tags.find_all('span')
            tags = [tag.text for tag in tags]
        elif col_name=="Tags":
            tags2 = col.find('td')
            tags2 = tags2.find_all('span')
            for tag in tags2 :
                tags.append(tag.text)
        elif col_name== "사이트":
            site_name = col.find('td').text
            tags.append(site_name)
        elif col_name=='Category ID':
            CATEGORY_ID = col.find('td').text

    # indented block 가져오기
    indented_divs = article.find_all('div', 'indented')
    # h1 이면서 자식이 summary 가져오기
    all_h1 = article.find_all('h1')
    all_indent_h1 = []
    for idx, h1 in enumerate(all_h1):
        if '<details>' in str(all_h1[idx]):
            all_indent_h1.append(all_h1[idx])
    for h1_idx, indent_h1 in enumerate(all_indent_h1):    
        for idx, sibling in enumerate(all_indent_h1[h1_idx].next_siblings):
            # 바로 다음의 형제가 indented div 라면
            if idx == 0 and '<div class="indented"' in str(sibling):
                details = all_indent_h1[h1_idx].find("details")
                details.append(sibling)
                summary = details.find("summary")
                summary.name = "h1"
                summary.wrap(soup.new_tag('summary', **{'class':'Notion_summary_h1'}))
                all_indent_h1[h1_idx].unwrap()
    # h2 이면서 자식이 summary 가져오기
    all_h2 = article.find_all('h2')
    all_indent_h2 = []
    for idx, h2 in enumerate(all_h2):
        if '<details>' in str(all_h2[idx]):
            all_indent_h2.append(all_h2[idx])
    for h2_idx, indent_h2 in enumerate(all_indent_h2):    
        for idx, sibling in enumerate(all_indent_h2[h2_idx].next_siblings):
            # 바로 다음의 형제가 indented div 라면
            if idx == 0 and '<div class="indented"' in str(sibling):
                details = all_indent_h2[h2_idx].find("details")
                details.append(sibling)
                summary = details.find("summary")
                summary.name = "h2"
                summary.wrap(soup.new_tag('summary', **{'class':'Notion_summary_h2'}))
                all_indent_h2[h2_idx].unwrap()
    # h3 이면서 자식이 summary 가져오기
    all_h3 = article.find_all('h3')
    all_indent_h3 = []
    for idx, h3 in enumerate(all_h3):
        if '<details>' in str(all_h3[idx]):
            all_indent_h3.append(all_h3[idx])
    for h3_idx, indent_h3 in enumerate(all_indent_h3):    
        for idx, sibling in enumerate(all_indent_h3[h3_idx].next_siblings):
            # 바로 다음의 형제가 indented div 라면
            if idx == 0 and '<div class="indented"' in str(sibling):
                details = all_indent_h3[h3_idx].find("details")
                details.append(sibling)
                summary = details.find("summary")
                summary.name = "h3"
                summary.wrap(soup.new_tag('summary', **{'class':'Notion_summary_h3'}))
                all_indent_h3[h3_idx].unwrap()
    
    # tags는 배열 형태이므로 comma로 구분되는 문자열 값으로 변환
    tags_str = ''
    for tag in tags:
        tags_str += tag+', '
    tags_str = tags_str[:-2]

    # 제목 문자열 가져오고, 해당 태그는 제거
    title = article.find('h1', class_='page-title')
    title_text = title.text
    title.extract()
    
    # img base64로 변환하여 업로드
    all_img_columns = article.find_all('img')
    img_columns = []
    for i, img_column in enumerate(all_img_columns):
        if not ('http' in img_column['src'] or 'ico' in img_column['src']):
            img_columns.append(img_column)
    
    if img_columns != 0:
        for img_column in img_columns:
            modified_img_path = img_column['src'].replace("%5B", '[').replace("%5D", ']').replace("%20", ' ')
            im_b64 = base64.b64encode(
                open(f"{path_list[html_idx]}/{modified_img_path}","rb").read()
            ).decode('utf-8')
            img_column['src'] = f"data:image/png;base64,{im_b64}"
        
    # 카테고리 값 받아오기 

    # 블로그 카테고리 ID 가져오기
    ACCESS_TOKEN = config["ACCESS_TOKEN"]
    BLOG_NAME = config["BLOG_NAME"]
    url = 'https://www.tistory.com/apis/category/list'
    params = {
        'access_token': ACCESS_TOKEN,
        'blogName': BLOG_NAME,
        'output': 'lxml'
    }
    resp = requests.get(url, params=params)

    soup_category = BeautifulSoup(resp.text, 'lxml')
    category_list = soup_category.find_all('category')

    def get_category_id_from_label(target_name):
        url = "https://www.tistory.com/apis/category/list"

        params = {
            'access_token': ACCESS_TOKEN,
            'blogName': BLOG_NAME,
            'output': 'lxml'
        }
        # api 요청
        resp = requests.get(url, params=params)
        
        # lxml 형식으로 parsing
        soup_category = BeautifulSoup(resp.text, 'lxml')
        
        # category로 되어있는 모든 태그 가져오기
        category_list = soup_category.find_all('category')
        
        # 모든 category 탐색
        for item in category_list:
            label = item.find('label').text
                # 찾고자 하는 target_name을 발견하면 id 반환
            if label == target_name:
                return item.find('id').text

    CATEGORY_ID = get_category_id_from_label(CATEGORY)

    # 게시물 업로드
    ACCESS_TOKEN = config["ACCESS_TOKEN"]
    BLOG_NAME = config["BLOG_NAME"]
    url = 'https://www.tistory.com/apis/post/write'
    data = {
        'access_token': ACCESS_TOKEN,
        'blogName': BLOG_NAME,
        'output': 'lxml',
        'title': title.get_text(),
        'content': soup,
        # 0은 비공개 1은 보호 3은 발행
        'visibility': '3',
        'category': CATEGORY_ID,
        'tag':tags_str
    }
    
    # 업로드 요청
    resp = requests.post(url, data=data)
    # 게시글 업로드 요청 여부 확인
    stat = resp.status_code
    if stat == 200 :
        print(f"({title}) 업로드 완료")
        if config["REMOVE_AFTER_UPLOAD"] and os.path.isdir(f"./{path_list[html_idx]}"):
            shutil.rmtree(f"./{path_list[html_idx]}")
            print(f"{path_list[html_idx]} 폴더 제거 완료")
    else :
        print(f"Error Code {stat} : {title} 업로드 실패")