import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import datetime
import json


def selectRequestUrl(url):
    request = requests.get(url)
    response = json.loads(request.content)
    return response


def get_AWS_status(region):
    print("parou aqui no início mesmo")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")

    region = region.lower()

    data = {
        "request_status": {"status": 200, "description": "Ok"},
        "metadata": {
            "region": region.capitalize(),
            "query_time": datetime.datetime.now().isoformat(),
        },
        "services": {},
    }

    print("tem o drivere", chrome_options)

    def getEventInfo(cell):
        div_button = cell.find_element(By.CSS_SELECTOR, "div[role='button']")
        if div_button.get_attribute("aria-label").strip() == "No Reported Event":
            event_info = {"status": "No Reported Event"}
        else:
            driver.execute_script("arguments[0].click();", div_button)
            event_info = {
                "title": cell.find_element(By.CLASS_NAME, "popover-content-layout")
                .find_element(By.TAG_NAME, "h2")
                .text,
                "status": cell.find_element(By.CLASS_NAME, "popover-content-layout")
                .find_element(By.TAG_NAME, "span")
                .text,
                "summary": cell.find_element(By.CLASS_NAME, "popover-content-layout")
                .find_element(By.TAG_NAME, "p")
                .text,
                "description": cell.find_element(
                    By.CLASS_NAME, "popover-content-layout"
                )
                .find_element(By.TAG_NAME, "div")
                .text,
            }
        return event_info

    with webdriver.Chrome(options=chrome_options) as driver:
        print("parou aqui no início")
        try:
            driver.get("https://health.aws.amazon.com/health/status")
            revealed = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, "awsui_row_wih1l_1l1xk_301")
                )
            )

            print("consegiuu carregar pagina")

            input_element = driver.find_element(
                By.XPATH, '//input[@aria-label="Find an AWS service or Region"]'
            )
            input_element.send_keys(f"Region = {region}")
            input_element.send_keys(Keys.ENTER)

            print("consegiuu colocar regiao")

            link = driver.find_element(
                By.XPATH,
                '//div[@class="awsui_footer-wrapper_wih1l_1l1xk_280 awsui_variant-container_wih1l_1l1xk_161"]/div/span/div/a',
            )
            driver.execute_script("arguments[0].click();", link)

            print("consegiuu mostrar todas as linhas da regiao")

            tr_header = driver.find_element(By.TAG_NAME, "tr")
            columns = [i.text for i in tr_header.find_elements(By.TAG_NAME, "th")]

            print("consegiuu pegar todas as linhas da regiao")

            columns = [
                item
                for item in columns
                if item != "RSS" and item != "" and item != "Service"
            ]

            trs = driver.find_elements(By.TAG_NAME, "tr")[1:]
            for row in trs:
                cells = row.find_elements(By.TAG_NAME, "td")

                if cells:
                    row_data = [cells[0].text.strip()] + [
                        getEventInfo(cell)
                        if cell.find_elements(By.CSS_SELECTOR, "div[role='button']")
                        else ""
                        for cell in cells[1:]
                    ]
                    row_data = [item for item in row_data if item != ""]

                    data["services"][row_data[0]] = dict(zip(columns, row_data[1:]))
            print("rodou o for de boas")
        except Exception as error:
            print("parou aqui no erro")
            data["request_status"]["status"] = 404
            data["request_status"]["description"] = "Bad request: " + error

        driver.quit()

    data_json = json.dumps(data)
    print("parou aqui no fim")
    return data_json
