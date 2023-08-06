"""
這是直接針對cakeresume.py的檔案延伸的作業
要先行準備想要做的公司的名字與codeName(cakeresume針對各公司在url的代稱)
可讀取過往爬過的資訊，有新增工作資料，則進行line通知
"""

import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

def getSoup(url):
    """
    回傳連線的soup，若無則回傳空值
    """
    resp = requests.get(url)
    if resp.status_code != 200:
        print('URL發生錯誤：' + url)
        return
    
    return BeautifulSoup(resp.text, 'html.parser')
def findDetails(soup):
    """
    從soup找出職缺資訊
    職缺列表，內容包含: 職缺名稱 / 連結 / po職缺時間 / 多少人看過 / 薪水(在cakeresume上不穩定，就不抓了)
    return [dictionary1, dictionary2, ...]
    """
    jobs = []

    jobList = soup.find_all("div", "CompanyJobItemWithAdminTool_container__bMESq")

    for jobDetails in jobList:
        title = jobDetails.find("div", "CompanyJobItemView_title__UheeT CompanyJobItemView_desktop__NNXw3").a.text
        url = jobDetails.find("div", "CompanyJobItemView_title__UheeT CompanyJobItemView_desktop__NNXw3").a["href"]
        date = jobDetails.find("div","CompanyJobItemView_leftColumn___ksQ_").find("div", "InlineMessage_label__hP3Fk").text
        competeCount = jobDetails.find("div", "Tooltip_handle__PbVuc").text
        # salary = jobDetails.find("div", "CompanyJobItemView_rightColumn__QisBq").find_all("div", "InlineMessage_inlineMessage__I9C_W InlineMessage_inlineMessageLarge__yeH0A InlineMessage_inlineMessageDark__rNo_a")[2].text
        jobs.append({"title":title,"url": url,"date": date,"competeCount": competeCount})

    return jobs

def cakeresume(codeName):
    '''
    當正確輸入的時候，會回傳所有工作職缺列表，以list的方式呈現
    '''

    url = f"https://www.cakeresume.com/companies/{codeName}/jobs"

    soup = getSoup(url)
    if not soup:
        return

    lastPage = int(soup.find_all("button", "Pagination_itemNumber__5L1fV")[-1].text)

    jobs = []
    for i in range(lastPage):
        page = i + 1
        if page != 1:
            soup = getSoup(url+f"?page={page}")
        
        jobs += findDetails(soup)

    return jobs

def dfToString(notify_df, companyName):
    result_String = f"\n {companyName}\n"
    result_String += "*****\n"
    for jobDetails in notify_df.values:
        
        # 處理每一筆新增的工作資訊
        temp = ""
        for content in jobDetails:
            temp += content + "\n"
        result_String += (temp) + "-----\n"
    result_String += "*****\n"   
    return result_String

def notifyWithLine(result_String):
    line_token = os.environ.get("line_token")
    headers = { "Authorization": "Bearer " + line_token }
    data = { 'message': result_String }
    requests.post("https://notify-api.line.me/api/notify",headers = headers, data = data)

if __name__ == "__main__":
    
    # "companyList.csv": 先前抓的公司相關資料，可自行補充
    with open("companyList.csv") as f:
        
        for i in f.readlines():
            codeName, companyName = i.strip().split(",")
            
            old_df = pd.DataFrame(None)
            
            # 檢查是否之前有做過爬蟲該公司的資料，並讀取他
            if os.path.exists(f"{codeName}.csv"):
                old_df = pd.read_csv(f"{codeName}.csv")
            
            jobs = cakeresume(codeName)
            jobs_df = pd.DataFrame(jobs)

            # 做完馬上更新CSV檔，供下次使用
            jobs_df.to_csv(f"{codeName}.csv", index=False)
                
            # 若之前沒有爬蟲過該公司的資料，顯示於terminal，不做line的通知
            if old_df.size == 0:
                for line in jobs_df.values:
                    print(line)
                continue
            
            # 開始比對是否有新增的工作資訊，並於line做通知
            compare_column = 'title'
            merged_df = jobs_df.merge(old_df[[compare_column]], on=compare_column, how='left', indicator=True)
            
            # 用left join的方式區分哪些是新的工作資料
            notify_df = merged_df[merged_df["_merge"] == "left_only"]
                        
            if notify_df.size == 0:
                print(f"{companyName}沒有新增的工作資訊，不做通知")
                continue
            else:
                notify_df = notify_df.drop(columns="_merge")
                result_String = dfToString(notify_df, companyName)
                
                # 進行新的工作通知
                notifyWithLine(result_String)