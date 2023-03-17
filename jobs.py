import time  # for time delaying
#import pandas as pd  # for dataframe
from selenium import webdriver  # to allow automation on webdriver (e.g. chrome, mozilla, edge)
from selenium.webdriver.chrome.options import Options  # to adjust the option of webdriver
from webdriver_manager.chrome import ChromeDriverManager  # to use google chrome
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException  # To handle error
from selenium.webdriver.common.keys import Keys  # to emulate keypress
from selenium.webdriver.common.by import By  # for finiding element
import re  # regex
from tqdm.notebook import tqdm  # track progress
import threading  # multithreading

# Hide warnings
import logging
import os
import warnings

warnings.filterwarnings('ignore')
logging.getLogger('WDM').setLevel(logging.NOTSET)
os.environ['WDM_LOG'] = "false"


# driver = webdriver.Chrome(ChromeDriverManager().install())
# driver.set_window_size(1120, 1000)
# options.add_argument('headless')

def collect_jobs(job_name, jobs_no=None, location=None, headless=True, driver_no=4):
    """

    """
    chrome_options = None
    if headless:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
    main_driver = _collect_jobs(job_name, location, chrome_options)

    # Get number of pages
    footer = main_driver.find_element(By.CLASS_NAME, 'paginationFooter')
    page_no = int(footer.text.split()[-1])

    # If number of jobs is specified only get upper(jobs_no/30) pages
    if jobs_no is not None:
        page_no = min(page_no, (jobs_no + 29) // 30)

    lst = []
    threads = []
    for pn in tqdm(range(1, page_no + 1), desc="Page number"):
        current_url = main_driver.current_url
        try:
            next_page = main_driver.find_element(By.XPATH, '//div[@class="pageContainer"]//span[@alt="next-icon"]')
            next_page.click()
        except:
            pass
        t = threading.Thread(target=jobs_detail, args=(current_url, lst, chrome_options))
        t.start()
        threads.append(t)
        time.sleep(2)

        if len(threads) == driver_no:
            threads.pop(0).join()

    for thread in threads:
        thread.join()
    return lst


def _collect_jobs(job, location=None, option=None):
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
    driver.set_window_size(1120, 1000)
    # Go to glassdoor
    driver.get('https://www.glassdoor.com.au/Job')
    time.sleep(5)
    # Get the search bar for job and location
    search_job = driver.find_element(By.XPATH, '//*[@id="sc.keyword"]')
    search_location = driver.find_element(By.XPATH, '//*[@id="sc.location"]')

    # If location is not defined, do nothing
    if location is not None:
        search_location.clear()
        search_location.send_keys(location)

    # Find job
    search_job.clear()
    search_job.send_keys(job, Keys.RETURN)

    close_signup(driver)

    return driver


def close_signup(driver):
    time.sleep(2)
    try:
        driver.find_element(By.XPATH, '//*[@id="MainCol"]/div[1]/ul/li[1]').click()
    except:
        pass

    time.sleep(2)

    try:
        driver.find_element(By.XPATH, '//*[@id="JAModal"]/div/div[2]/span').click()
    except:
        #         print('No Signup')
        pass


def job_get_salary(job):
    time.sleep(1)
    temp = job.find_element(By.XPATH, '//div[contains(@class,"salaryTab tabSection")]/div[1]/div[1]')
    if temp.text == "Estimate provided by employer":
        temp = job.find_element(By.XPATH, '//div[contains(@class,"salaryTab tabSection")]/div[1]/div[2]')
    sal = re.split('\n|/', temp.text)
    return (sal[0].strip(), sal[-2].strip(), sal[-1].strip())  # Estimate, Low, High


# def job_get_desc(job):
#     try:
#         job.find_element(By.XPATH,'//*[@id="JobDescriptionContainer"]/div[2][text()="Show More"]').click()
#     except:
#         pass
#     time.sleep(0.1)
#     requirements = job.find_elements(By.XPATH, '//*[@class="jobDescriptionContent desc"]//ul')
#     job_descriptions = []
#     for req in requirements:
#         job_descriptions += req.text.split('\n')
#     return job_descriptions

def job_get_desc(job):
    try:
        job.find_element(By.XPATH, '//*[@id="JobDescriptionContainer"]/div[2][text()="Show More"]').click()
    except:
        pass
    time.sleep(1)
    requirements = job.find_element(By.XPATH, '//*[@class="jobDescriptionContent desc"]')
    return requirements.text


def job_get_company_overview(job):
    comp_size = comp_type = comp_sector = comp_founded = comp_industry = comp_revenue = -1
    keyword = ["Size", "Type", "Sector", "Founded", "Industry", "Revenue"]
    variables = [comp_size, comp_type, comp_sector, comp_founded, comp_industry, comp_revenue]
    overview = job.find_element(By.XPATH, '//*[@id="EmpBasicInfo"]//*[text()="Company Overview"]/../div')
    for var in range(len(keyword)):
        try:
            xp = './/*[text()="' + keyword[var] + '"]/following-sibling::span'
            variables[var] = overview.find_element(By.XPATH, xp).text
        except:
            pass
    return variables


def get_company_element(root, xp):
    try:
        result = root.find_element(By.XPATH, xp).text
    except:
        result = None
    return result


def get_company_ratings(job):
    comp_rating = comp_rec_friend = comp_app_ceo = comp_rater = comp_car_opp = comp_compben = comp_cultval = comp_senmng = comp_wlb = None
    try:
        root = job.find_element(By.XPATH, '//*[@id="employerStats"]/..')

        comp_rating = get_company_element(root, './/*[@data-test = "rating-info"]/div[1]')
        comp_rec_friend = get_company_element(root, './/*[text()="Recommend to a friend"]/../div[1]')
        comp_app_ceo = get_company_element(root, './/*[text()="Approve of CEO"]/../div[1]')
        comp_rater = get_company_element(root, './/*[text()="Recommend to a friend"]/../div[1]/../../div[3]')

        try:
            root = root.find_element(By.XPATH, './/span[text()="Career Opportunities"]/..')
            comp_car_opp = get_company_element(root, './span[3]')
            comp_compben = get_company_element(root, './span[6]')
            comp_cultval = get_company_element(root, './span[9]')
            comp_senmng = get_company_element(root, './span[12]')
            comp_wlb = get_company_element(root, './span[15]')
        except:
            pass
    except:
        pass

    return (
        comp_rating, comp_rec_friend, comp_app_ceo, comp_rater, comp_car_opp, comp_compben, comp_cultval, comp_senmng,
        comp_wlb)


def jobs_detail(page_url, lst, option=None, driver=None):
    time.sleep(2)
    if driver == None:
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
        driver.set_window_size(1120, 1000)

    driver.get(page_url)
    time.sleep(5)
    close_signup(driver)
    jobs = driver.find_elements(By.XPATH, '//*[@id="MainCol"]/div[1]/ul/li')
    _jobs_detail(lst, jobs)
    driver.quit()


def _jobs_detail(lst, jobs):
    time.sleep(2)
    for job in tqdm(jobs, desc="Jobs number"):
        job_title = -1
        location = -1
        company = -1
        job_url = -1
        job_descriptions = -1
        # Salary
        base_salary_estimate = base_salary_low = base_salary_high = -1
        # Job overviews
        comp_size = comp_type = comp_sector = comp_founded = comp_industry = comp_revenue = None
        # Company ratings
        comp_rating = comp_rec_friend = comp_app_ceo = comp_rater = comp_car_opp = comp_compben = comp_cultval = comp_senmng = comp_wlb = None

        # Get the job title, location, company name, job url
        time.sleep(1)
        try:
            job_title = _get_attribute(job, 'data-normalize-job-title')
        except:
            pass

        try:
            location = _get_attribute(job, 'data-job-loc')
        except:
            pass
        try:
            job_child = job.find_element(By.XPATH, 'div[1]/a')
            company = _get_attribute(job_child, 'title')
            job_url = _get_attribute(job_child, 'href')
        except:
            pass

        job_clicked = False
        try:
            job.click()
            time.sleep(1)
            job_clicked = True
        except:
            time.sleep(1)
            print("!", end=" ")

        if job_clicked:
            # If there's no simplified title

            if not isinstance(job_title, str):
                time.sleep(1)
                try:
                    xp = '//*[@id="JDCol"]/div/article/div/div[1]/div/div/div[1]/div[3]/div[1]/div[2]'
                    job_title = job.find_element(By.XPATH, xp).text
                    print("New Title:", job_title, end=" ")
                except:
                    pass

            # Get the salary estimate
            try:
                (base_salary_estimate, base_salary_low, base_salary_high) = job_get_salary(job)
            except:
                print("No Salary Info", end=" ")

            # Get job description
            try:
                job_descriptions = job_get_desc(job)
            except:
                print("No Job Requirement Found", end=" ")

            # Get job overviews
            try:
                (comp_size, comp_type, comp_sector, comp_founded, comp_industry,
                 comp_revenue) = job_get_company_overview(job)
            except:
                print("No Job overviews", end=" ")

            # Get company ratings
            try:
                ratings = get_company_ratings(job)
                (comp_rating, comp_rec_friend, comp_app_ceo, comp_rater, comp_car_opp, comp_compben, comp_cultval,
                 comp_senmng, comp_wlb) = ratings
            except:
                print("No Ratings", end=" ")

            lst.append({
                "Job Title": job_title,
                "Job Location": location,
                "Company": company,
                "Url": job_url,
                "Estimate Base Salary": base_salary_estimate,
                "Low Estimate": base_salary_low,
                "High Estimate": base_salary_high,
                "Company Size": comp_size,
                "Company Type": comp_type,
                "Company Sector": comp_sector,
                "Company Founded": comp_founded,
                "Company Industry": comp_industry,
                "Company Revenue": comp_revenue,
                "Job Descriptions": job_descriptions,
                "Company Rating": comp_rating,
                "Company Friend Reccomendation": comp_rec_friend,
                "Company CEO Approval": comp_app_ceo,
                "Companny Number of Rater": comp_rater,
                "Company Career Opportinities": comp_car_opp,
                "Compensation and Benefits": comp_compben,
                "Company Culture and Values": comp_cultval,
                "Company Senior Management": comp_senmng,
                "Company Work Life Balance": comp_wlb
            })


#
def _get_attribute(job, attribute):
    time.sleep(0.1)
    try:
        result = job.get_attribute(attribute)
    except:
        result = -1
    return result


locations = ["Victoria", "New South Wales", "Northern Territory", "Queensland",
             "South Australia", "Tasmania", "Western Australia"]

for loc in tqdm(locations, desc="States"):
    jobs = collect_jobs("Data Science", location=loc + ", Australia")
    jobs_df = pd.DataFrame(jobs)
    jobs_df.to_csv(loc + ".csv", index=False)
