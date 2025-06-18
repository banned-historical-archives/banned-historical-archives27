import requests
import tempfile
import sys
import json
import hashlib
from urllib.parse import urlparse
import os
from bs4 import BeautifulSoup
import time

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0',
'Host': 'www.cia.gov',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
'Accept-Language': 'en-US,en;q=0.5',
'Accept-Encoding': 'gzip, deflate, br, zstd',
'Connection': 'keep-alive',
'Upgrade-Insecure-Requests': '1',
'Sec-Fetch-Dest': 'document',
'Sec-Fetch-Mode': 'navigate',
'Sec-Fetch-Site': 'cross-site',
'DNT': '1',
'Sec-GPC': '1',
'Priority': 'u=0, i',
'Pragma': 'no-cache',
'Cache-Control': 'no-cache',
}

local_socks5_proxy = os.environ.get('HTTP_PROXY')
proxy=local_socks5_proxy # 传入代理
# 配置代理
proxies = {
    'http': proxy,
    'https': proxy
} if proxy else None
def safe_get(url, params):
    while True:
        try:
            response = requests.get(url, params=params, proxies=proxies, headers=headers, timeout=10)
            if len(response.history) > 0:
                print('!!!403')
                sys.exit(0)
            response.raise_for_status()  # 检查HTTP请求是否成功
            response_text = response.text
            return response_text
        except Exception as e:
            print('reload', url)
            time.sleep(2)


def fetch_search_results_with_proxy(keyword):
    """

    Args:
        query (str): 搜索关键词。
        start_page (int): 起始页码。
        end_page (int): 结束页码。
        document_date_end (str, optional): 文档结束日期，格式YYYY-MM-DD。默认为 None。
        proxy (str, optional): SOCKS5代理地址，例如 'socks5h://localhost:11999'。默认为 None。

    Returns:
        list: 包含所有抓取到的搜索结果的列表。
    """
    base_url = "https://www.cia.gov"
    search_url = base_url + "/readingroom/advanced-search-view"

    page = 1
    while True:
        params = {
    "keyword": keyword,
    "label": "",
    "sm_field_document_number": "",
    "sm_field_original_classification": "",
    "ds_field_pub_date_op": "=",
    "ds_field_pub_date[value]": "",
    "ds_field_pub_date[min]": "",
    "ds_field_pub_date[max]": "",
    "sm_field_content_type": "",
    "sm_field_case_number": "",
            "page": page - 1,
        }

        print(f"正在抓取第 {page} 页 (通过代理: {proxy if proxy else '无'})...")
        try:
            # 发送请求时传入proxies和headers参数

            md5_hash = hashlib.md5((search_url + json.dumps(params)).encode('utf-8')).hexdigest()

            html_list_name = os.path.join(os.getcwd(), 'html_list', md5_hash[:4], md5_hash + '.html')

            print(md5_hash)
            response_text = ''
            if os.path.exists(html_list_name):
                print('ignore', md5_hash)
                with open(html_list_name, 'r', encoding='utf-8') as file:
                    response_text = file.read()
            else:
                response_text = safe_get(search_url, params)
                if not os.path.exists(os.path.dirname(html_list_name)):
                    os.makedirs(os.path.dirname(html_list_name))
                safe_write(html_list_name, response_text)

            soup = BeautifulSoup(response_text, 'html.parser')

            links = soup.select("tbody .views-field a") 

            if len(links) == 0:
                print('empty')
                break

            for i in links:
                link = i['href']

                fetch_detail(base_url + link, keyword)

            #time.sleep(2)  # 礼貌性延迟，避免给服务器造成过大压力

        except requests.exceptions.ProxyError as e:
            print(f"代理连接错误，请检查代理设置和网络连接: {e}")
            break # 代理错误则停止
        except requests.exceptions.RequestException as e:
            print(f"请求第 {page} 页时发生错误: {e}。状态码：{response.status_code if 'response' in locals() else '未知'}")
            break # 出现其他请求错误则停止抓取
        except Exception as e:
            print(f"解析第 {page} 页时发生错误: {e}")
            break
        page += 1

def safe_write(f, c):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_f:
        temp_f.write(c)
        temp_f.flush()
        os.fsync(temp_f.fileno()) 

    temp_file_path = temp_f.name
    os.replace(temp_file_path, f)

def fetch_detail(link, key = None):
    fname = hashlib.md5(link.encode('utf-8')).hexdigest()
    directory = os.path.join(os.getcwd(), 'html', fname[:4])
    output = os.path.join(directory, fname + '.html')
    content = ''
    if os.path.exists(output):
        print('ignore', link)
        return
        with open(output, 'r', encoding='utf-8') as file:
            content = file.read()
    else:
        print('fetch', link, fname)
        content = safe_get(link, {})
    if key:
        if content.lower().find(key) == -1:
            if os.path.exists(output):
                os.unlink(output)
            return
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    safe_write(output,content)

if __name__ == "__main__":
    for i in [
        "deng xiaoping",
        "mao zedong",
        'jiang qing',
        'mao yuanxin','gang of four','mao tse-tung','hsiao-ping'
    ]:
        print(i)
        fetch_search_results_with_proxy(
            i,
        )
