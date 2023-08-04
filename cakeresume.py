import requests
from bs4 import BeautifulSoup

def getSoup(url):
    """
    回傳連線的soup，若無則回傳空值
    """
    resp = requests.get(url)
    if resp.status_code != 200:
        print('URL發生錯誤：' + url)
        return
    
    return BeautifulSoup(resp.text, 'html5lib')

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

def getCodeName(name, isCodeName = False):
    """
    使用者輸入公司名稱
    若正確則回傳公司的codeName
    若自行輸入codeName，則直接回傳codeName
    """
    if isCodeName:
        return name

    url = f"https://www.cakeresume.com/companies?q={name}"
    soup = getSoup(url)
    if not soup:
        return

    companyList = soup.find_all("a", "CompanySearchItem_companyTitle___yld2")
    for company in companyList:
        companyName = company.text
        url = f"https://www.cakeresume.com{company['href']}"
        print(companyName, url)
        if input("正確請輸入'y': ") != "y":
            continue
        codeName = url.split("/")[-1]
        return codeName
    print("沒找到正確的公司，請自行上網找尋codeName")
    return 

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
    

if __name__ == "__main__":
    name_ = input("若你有codeName，請輸入'y'，否則請輸入公司名稱: ")
    codeName = None
    if name_ == "y":
        codeName = input("請輸入cakeresume的codeName: ")
    else:
        codeName = getCodeName(name_)

    # 主邏輯執行的地方
    try:
        jobs = cakeresume(codeName)
        for job in jobs:
            print(job)
    except Exception as e:
        print("codeName輸入錯誤或者找不到該公司的資料")
    

        