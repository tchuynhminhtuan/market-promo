
import csv
import os
import os.path
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import logging
import re
from pyvirtualdisplay import Display
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


# Start a virtual display
display = Display(visible=0, size=(1920, 1080))
display.start()

now = datetime.now().date()


# Chrome
def chrome_drive():

    # Configure Chrome options
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
    options.add_argument('--no-sandbox')  # Bypass OS security model
    options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems

    # Create a driver instance
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


    options.add_experimental_option("mobileEmulation",
                                    {"deviceMetrics": {"width": 428, "height": 926, "pixelRatio": 3.0}})

    # wait for the page to be fully loaded before proceeding
    options.page_load_strategy = 'normal'  # 'none', 'eager', or 'normal'


    # Disable the "Chrome is being controlled by automated test software" notification
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # # Disable the "navigator.webdriver" property
    options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

    # Disable the "Chrome is being controlled by automated test software" banner
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Maximize the window to avoid fingerprinting based on screen resolution
    options.add_argument("start-maximized")

    # Disabling the Automation Extension can help prevent detection as an automated script and increase the chances of
    # successfully completing your automation tasks.
    options.add_experimental_option('useAutomationExtension', False)

    # This argument tells the browser to ignore any SSL certificate errors that may occur while accessing a website,
    # which is useful when testing on a site with a self-signed or invalid SSL certificate. Without this argument,
    # the browser will display a warning message about the certificate and require manual confirmation to proceed.
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors=yes')

    prefs = {
        "disable-transitions": True,
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2
    }
    options.add_experimental_option("prefs", prefs)

    return driver


class FPT:

    def ensure_internet_connection(self):
        import socket
        def is_internet_connected():
            try:
                socket.create_connection(("8.8.8.8", 53), timeout = 5)
                return True
            except OSError:
                return False

        # wait_duration=30
        # def wait_for_specific_duration(duration):
        #     start_time=time.time()
        #     while time.time() - start_time < duration:
        #         time.sleep(1)

        max_attempts=300
        retry_interval=5

        # Attempt to establish internet connection
        for attempt in range(1, max_attempts + 1):
            if is_internet_connected():
                return True
            else:
                print(
                    f"No internet connection. Retrying in {retry_interval} seconds... (Attempt {attempt}/{max_attempts})")
                time.sleep(retry_interval)

        # If internet connection couldn't be established, wait for disruption and a specific duration
        print(f"No internet connection after {max_attempts} attempts. Waiting for disruption...")
        while is_internet_connected():
            time.sleep(1)

        return True

    def fpt(self, link_check: list, restart_link: str):


        data_list = []

        driver = chrome_drive()

        # driver = firefox_drive()

        wait = WebDriverWait(driver, 20)
        actions = ActionChains(driver)

        base_path = '/content'
        output_dir = os.path.join(base_path, f"{now}")
        output_img = os.path.join(output_dir, 'img')

        def record():
            # Define the base path to Google Drive folder
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            file_path = os.path.join(output_dir, f"1-fpt-{now}.csv")

            with open(file_path, "a") as file:
                writer = csv.DictWriter(file,
                                        fieldnames=["Product_Name", "Ton_Kho", "Gia_Niem_Yet", "Gia_Khuyen_Mai", "Date",
                                                    "Khuyen_Mai", "Thanh_Toan", "Link"], delimiter=";")
                if os.stat(file_path).st_size == 0:
                    writer.writeheader()
                for row in data_list:
                    writer.writerow(row)

        def screen_shot(product_name):
          if not os.path.exists(output_img):
              os.makedirs(output_img)
          product_name_new=product_name.replace("/", "")
          driver.fullscreen_window()
          driver.set_window_size(1920, 2080)
          driver.get_screenshot_as_png()
          if not os.path.exists(f"{output_img}/{product_name_new}_{now}.png"):
              driver.save_screenshot(f"{output_img}/{product_name_new}_{now}.png")
          else:
              driver.save_screenshot(f"{output_img}/{product_name_new}_{now}_latest.png")

        def check_price():

            try:
                button_cash_discount = driver.find_elements(By.CSS_SELECTOR, ".st-boxPromo__list .radio")
                count_button = 0
                for button in button_cash_discount:
                    count_button += 1
                    if ("đ" in button.text.lower()) and not any(substring in button.text.lower() for substring in ['góp', 'tặng']):
                        # Scroll the element into view using JavaScript
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(.2)
                        actions.move_to_element(button).perform()
                        actions.click(button).perform()
                        time.sleep(5)

                # If there are two cash discount, we have a problem
                button_cash_discount = driver.find_elements(By.CSS_SELECTOR, ".st-boxPromo__list .radio")
                if count_button > 1:
                    list_value = []
                    for button in button_cash_discount:
                        button_text = button.text.lower()
                        # Use a regular expression to find the numeric part
                        match = re.search(r'(\d{1,3}(?:,\d{3})*)(?=đ)', button_text)
                        if match:
                            extracted_value = match.group(1).replace(',','')
                            list_value.append(int(extracted_value))
                            print(match)
                        else:
                            print("Value not found")
                    # print(max(list_value))
                    if len(list_value) > 0:
                        final_cash_discount = button_cash_discount[list_value.index(max(list_value))]
                        print(final_cash_discount)
                        driver.execute_script("arguments[0].scrollIntoView();", final_cash_discount)
                        actions.move_to_element(final_cash_discount).perform()
                        actions.click(final_cash_discount).perform()
                        time.sleep(5)
                button_promos = driver.find_elements(By.XPATH, "//span[@class='ic-down-open-big']")
                print('button_promos: ', len(button_promos))
                for button_promo in button_promos:
                    wait.until(EC.element_to_be_clickable(button_promo))
                    driver.execute_script("arguments[0].scrollIntoView();", button_promo)
                    actions.move_to_element(button_promo).perform()
                    actions.click(button_promo).perform()
                    time.sleep(1)
            except NoSuchElementException:
                pass
            except IndexError:
                pass

            try:
                # This Class only appear when a product is in the Pre-Order process
                driver.find_element(By.CLASS_NAME, "st-banner__desc")
            except NoSuchElementException:
                try:
                    print("a try st-name class")
                    # wait.until(EC.visibility_of_element_located((By.XPATH,
                    #                                      "//h1[contains(@class, 'text-textOnWhitePrimary')]")))
                    driver.find_element(By.XPATH, "//h1[contains(@class, 'text-textOnWhitePrimary')]")
                except NoSuchElementException:

                    product_name = f"Please double check the link: {link}"

                    try:
                        # Try out if this product is being pre-ordered
                        driver.find_element(By.CLASS_NAME, "st-banner__btn")
                    except NoSuchElementException:
                        gia_niem_yet = 0
                        gia_khuyen_mai = 0
                        ton_kho = "No"
                        khuyen_mai = ""
                        thanh_toan = ""
                    else:
                        gia_niem_yet = "Pre-order"
                        gia_khuyen_mai = "Pre-order"
                        ton_kho = "No"
                        khuyen_mai = f"{link}"
                        thanh_toan = f"{link}"
                    new_data = {"Product_Name": product_name, "Ton_Kho": ton_kho, "Gia_Niem_Yet": gia_niem_yet,
                                "Gia_Khuyen_Mai": gia_khuyen_mai, "Date": now, "Khuyen_Mai": khuyen_mai,
                                "Thanh_Toan": thanh_toan, "Link": link}
                    data_list.append(new_data)
                    print(product_name)
                    screen_shot(product_name)

                else:
                    try:
                        # This class only appear when a product is being in preorder period or stopped selling.
                        special_note = driver.find_element(By.CLASS_NAME, "st-stt__noti")
                    except NoSuchElementException:
                        # from July 2nd, 2024, check storage

                        def save_each_storage():
                            product_name=(driver.find_element(By.XPATH,
                                                              "//h1[contains(@class, 'text-textOnWhitePrimary')]")
                            .text.strip().replace(
                                "Mini",
                                "mini").replace(
                                "Wi-Fi", "WiFi"))
                            to_remove_in_name=["Tai nghe ", "Thiết bị định vị thông minh ", "Bộ chuyển đổi "]
                            for item in to_remove_in_name:
                                if item in product_name:
                                    product_name=product_name.replace(item, "")
                            print(product_name)

                            # If the "mua" text in the class "st-pd-btn", the stock is "Yes"
                            try:
                                # buy_button = driver.find_element(By.CLASS_NAME, "st-pd-btn").text
                                buy_button=driver.find_element(By.XPATH,
                                                               "//div[@id='detail-buying-btns']/button[2]").text
                            except NoSuchElementException:
                                ton_kho="No"
                            else:
                                if "mua" in buy_button.lower():
                                    ton_kho="Yes"
                                else:
                                    ton_kho="No"

                            try:
                                driver.find_element(By.XPATH, "//div[contains(@class, 'TradePrice_tradePriceWrap__Sdms_')]/parent::div")
                            except NoSuchElementException:
                                khuyen_mai=""
                            else:
                                khuyen_mai=driver.find_element(By.XPATH,
                                                               "//div[contains(@class, 'TradePrice_tradePriceWrap__Sdms_')]/parent::div").text.strip()


                            # in the past, make a column of thanh_toan to specify and save thanh toan, but now, no longer
                            # need, July 1st, 2024
                            try:
                                # driver.find_element(By.CLASS_NAME, "st-boxFeature")
                                driver.find_element(By.XPATH,
                                                    "(//div[contains(@class, 'TradePrice_tradePriceWrap__Sdms_')]/following-sibling::div)[2]/div[2]")
                            except NoSuchElementException:
                                thanh_toan=""
                            else:
                                # Find the WebElement using Selenium
                                thanh_toan_xpath=driver.find_element(By.XPATH,
                                                                     "(//div[contains(@class, 'TradePrice_tradePriceWrap__Sdms_')]/following-sibling::div)[2]/div[2]")

                                # Get the HTML content of the WebElement
                                thanh_toan_html=thanh_toan_xpath.get_attribute('outerHTML')

                                # Parse the HTML content with BeautifulSoup
                                element=BeautifulSoup(thanh_toan_html, 'html.parser')

                                # Extract the text and replace "Xem chi tiết" with a newline character
                                thanh_toan=element.get_text(strip = True).replace("Xem chi tiết", "\n\n").replace("Xem tất cả", "\n\n")

                            try:
                                gia_khuyen_mai=driver.find_element(By.XPATH,
                                                                   "(//div[contains(@class, 'TradePrice_tradePriceWrap__Sdms_')]//span[contains(@class, 'h4-bold')])[1]").text.replace(
                                    "đ", "").replace("₫", "")
                            except NoSuchElementException:
                                gia_khuyen_mai= 'not trading'
                            print(gia_khuyen_mai)

                            try:
                                gia_niem_yet=driver.find_element(By.XPATH,
                                                                 "(//div[@class='TradePrice_tradePriceWrap__Sdms_']//div)[1]/div[1]/div[1]/span[contains(@class, 'line-through')]").text.replace("đ","").replace("₫", "")
                            except NoSuchElementException:
                                gia_niem_yet=gia_khuyen_mai

                            new_data={"Product_Name": product_name, "Ton_Kho": ton_kho, "Gia_Niem_Yet": gia_niem_yet,
                                      "Gia_Khuyen_Mai": gia_khuyen_mai, "Date": now, "Khuyen_Mai": khuyen_mai,
                                      "Thanh_Toan": thanh_toan, "Link": link}
                            data_list.append(new_data)
                            print(product_name)
                            screen_shot(product_name)

                        try:
                            driver.find_element(By.XPATH, "//span[text()='Dung lượng']/following-sibling::div//button")
                        except NoSuchElementException:
                            save_each_storage()

                        else:
                            storages = driver.find_elements(By.XPATH, "//span[text()='Dung lượng']/following-sibling::div//button")
                            for num in range(len(storages)):

                                storage = driver.find_element(By.XPATH,
                                                              f"(//span[text()='Dung lượng']/following-sibling::div//button)[{num+1}]")

                                driver.execute_script("arguments[0].scrollIntoView();", storage)
                                driver.execute_script("arguments[0].click();", storage)
                                time.sleep(2)
                                save_each_storage()
                    else:
                        # This is the case when the product is in the preorder process or stopped selling.
                        product_name = driver.find_element(By.CLASS_NAME, "st-name").text.strip().replace("Mini",
                                                                                                          "mini").replace(
                            "Wi-Fi", "WiFi")
                        to_remove_in_name = ["Tai nghe ", "Thiết bị định vị thông minh ", "Bộ chuyển đổi "]
                        for item in to_remove_in_name:
                            if item in product_name:
                                product_name = product_name.replace(item, "")

                        if "ngừng" in special_note.text.lower():
                            gia_niem_yet = "not trading"
                            gia_khuyen_mai = "not trading"
                            ton_kho = "not trading"
                            khuyen_mai = "not trading"
                            thanh_toan = "not trading"
                        else:
                            # this case of Pre-order period should be modify later (be aware of)
                            gia_niem_yet = 0
                            gia_khuyen_mai = 0
                            ton_kho = "No"
                            khuyen_mai = ""
                            thanh_toan = ""

                        new_data = {"Product_Name": product_name[:-14], "Ton_Kho": ton_kho, "Gia_Niem_Yet": gia_niem_yet,
                                    "Gia_Khuyen_Mai": gia_khuyen_mai, "Date": now, "Khuyen_Mai": khuyen_mai,
                                    "Thanh_Toan": thanh_toan, "Link": link}
                        data_list.append(new_data)
                        print(product_name)
                        screen_shot(product_name)

            else:
                # If a product is on the Pre-Order process, the stock is "No"
                product_name = driver.find_element(By.CLASS_NAME, "st-menu__logo").text.strip()
                ton_kho = "No"

                # The "st-boxPromo" Class is to check the promotion option
                try:
                    driver.find_element(By.CLASS_NAME, "st-boxPromo")
                except NoSuchElementException:
                    khuyen_mai = ""
                else:
                    khuyen_mai = driver.find_element(By.CLASS_NAME, "st-boxPromo").text.replace("Xem chi tiết",
                                                                                                "\n").strip()

                # The "st-boxFeature" Class is to check the payment option
                try:
                    driver.find_element(By.CLASS_NAME, "st-boxFeature")
                except NoSuchElementException:
                    thanh_toan = ""
                else:
                    thanh_toan = driver.find_element(By.CLASS_NAME, "st-boxFeature").text.replace("Xem chi tiết",
                                                                                                  "\n").strip()

                try:
                    gia_khuyen_mai = driver.find_elements(By.CLASS_NAME, "st-price-main")[-1].text
                except NoSuchElementException:
                    gia_khuyen_mai = 0
                print(gia_khuyen_mai)

                try:
                    gia_niem_yet = driver.find_element(By.CLASS_NAME, "st-price-sub").text
                except NoSuchElementException:
                    try:
                        gia_niem_yet = driver.find_element(By.CLASS_NAME, "st-price-main").text
                    except NoSuchElementException:
                        gia_niem_yet = gia_khuyen_mai

                new_data = {"Product_Name": product_name, "Ton_Kho": ton_kho, "Gia_Niem_Yet": gia_niem_yet,
                            "Gia_Khuyen_Mai": gia_khuyen_mai, "Date": now, "Khuyen_Mai": khuyen_mai,
                            "Thanh_Toan": thanh_toan, "Link": link}
                data_list.append(new_data)
                print(product_name)

                # Only screenshot the necessary products
                screen_shot(product_name)

        def open_other_tab():
            # Check the number of open tabs
            num_tabs = len(driver.window_handles)
            # print(f"Number of open tabs: {num_tabs}")
            if num_tabs > 1:
                pass
            else:
                driver.execute_script("window.open('https://fptshop.com.vn/')")
                actions.send_keys(Keys.COMMAND + 't')
                driver.switch_to.window(driver.window_handles[1])
                actions.send_keys('https://fptshop.com.vn/')
                time.sleep(1)
                actions.send_keys(Keys.RETURN)
                time.sleep(1)
                actions.perform()
                # switch back to the main window
                driver.switch_to.window(driver.window_handles[0])

        def login():
            # navigate to the Google login page
            driver.get("https://accounts.google.com/signin")

            # enter your Google account email and password
            email_input = driver.find_element(By.ID, "identifierId")
            time.sleep(3)
            email_input.click()
            time.sleep(1)
            email_input.send_keys("jakesully20002023@gmail.com")

            next_button = driver.find_element(By.XPATH, "(//span[@class='VfPpkd-vQzf8d'])[2]")
            next_button.click()
            time.sleep(5)

            wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@class='whsOnd zHQkBf'])[1]")))
            password_input = driver.find_element(By.XPATH, "(//input[@class='whsOnd zHQkBf'])[1]")
            password_input.click()
            time.sleep(2)
            password_input.send_keys("YesItIsJake")

            # click the sign-in button
            wait.until(EC.element_to_be_clickable((By.XPATH, "(//span[@class='VfPpkd-vQzf8d'])[2]")))
            signin_button = driver.find_element(By.XPATH, "(//span[@class='VfPpkd-vQzf8d'])[2]")
            signin_button.click()
            time.sleep(4)

        self.link_check = link_check
        self.restart_link = restart_link

        for link in self.link_check[self.link_check.index(self.restart_link):]:
            # open_other_tab()
            try:
                data_list=[]
                self.ensure_internet_connection()
                driver.get(link)
                time.sleep(7)
                check_price()
                record()
            except (WebDriverException, IndexError):
            # except ValueError:
            #     if WebDriverException:
            #         print(WebDriverException)
            #     elif TimeoutException:
            #         print(TimeoutException)
                driver.quit()
                print(datetime.now())
                print(f"Start again from link: {link}")
                self.restart_link = link
                self.fpt(self.link_check, self.restart_link)
            cookies = driver.get_cookies()
            print("cookies len: ", len(cookies))
            # print(cookies)
        driver.quit()


# FPT().fpt(link_check, link_check[0])
