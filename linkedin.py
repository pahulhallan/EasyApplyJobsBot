import time, math, random, os
import json

from selenium.webdriver.support.select import Select

import utils, constants, config
import pickle, hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
import yaml


class Linkedin:
    def __init__(self):
        utils.prYellow(
            "🤖 Thanks for using Easy Apply Jobs bot, for more information you can visit our site - www.automated-bots.com")
        utils.prYellow("🌐 Bot will run in Chrome browser and log in Linkedin for you.")

        # Load previously applied jobs
        self.applied_jobs_file = "data/applied_jobs.json"
        try:
            with open(self.applied_jobs_file, 'r') as f:
                self.already_applied = set(json.load(f))
            utils.prGreen(f"Loaded {len(self.already_applied)} previously applied jobs")
        except FileNotFoundError:
            self.already_applied = set()
            utils.prYellow("No previous applications found, starting fresh")

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                       options=utils.chromeBrowserOptions())
        # self.cookies_path = f"{os.path.join(os.getcwd(),'cookies')}/{self.getHash(config.email)}.pkl"
        self.driver.get('https://www.linkedin.com')

        if not self.isLoggedIn():
            self.driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
            utils.prYellow("🔄 Trying to log in Linkedin...")
            try:
                self.driver.find_element("id", "username").send_keys(config.email)
                time.sleep(2)
                self.driver.find_element("id", "password").send_keys(config.password)
                time.sleep(2)
                # remember_me_checkbox = self.driver.find_element("id", "rememberMeOptIn-checkbox")
                # if remember_me_checkbox.is_selected():  # If it's checked, uncheck it
                #     remember_me_checkbox.click()
                self.driver.execute_script("document.getElementById('rememberMeOptIn-checkbox').checked = false;")
                time.sleep(7)
                self.driver.find_element("xpath", '//button[@type="submit"]').click()
                time.sleep(30)
                utils.prGreen("🔄logged in Linkedin...")
            except:
                utils.prRed(
                    "❌ Couldn't log in Linkedin by using Chrome. Please check your Linkedin credentials on config files line 7 and 8.")

            # self.saveCookies()

        # Test Additional questions

        # start application

        self.linkJobApply()

    def getHash(self, string):
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def load_yaml_answers(self, file_path):
        with open(file_path, 'r') as file:
            answers = yaml.safe_load(file)
        return answers

    def loadCookies(self):
        if os.path.exists(self.cookies_path):
            cookies = pickle.load(open(self.cookies_path, "rb"))
            self.driver.delete_all_cookies()
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def saveCookies(self):
        pickle.dump(self.driver.get_cookies(), open(self.cookies_path, "wb"))

    def isLoggedIn(self):
        self.driver.get('https://www.linkedin.com/feed')
        try:
            self.driver.find_element(By.XPATH, '//*[@id="ember14"]')
            return True
        except:
            pass
        return False

    def generateUrls(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        try:
            with open('data/urlData.txt', 'w', encoding="utf-8") as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url + "\n")
            utils.prGreen("✅ Apply urls are created successfully, now the bot will visit those urls.")
        except:
            utils.prRed("❌ Couldn't generate urls, make sure you have editted config file line 25-39")

    def fill_out_additional_questions(self):
        try:
            time.sleep(random.uniform(1, constants.botSpeed))
            additional_questions = self.driver.find_elements(By.XPATH,
                                                             "//*[contains(text(), 'Additional Questions') or contains(text(), 'additional questions')]"
                                                             )
            # only apply to the values that are not entered, and add radio box
            if additional_questions and additional_questions[0].is_displayed():

                text_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input[type='text'], input:not([type]), textarea"
                )
                for input_field in text_inputs:
                    if input_field.is_displayed() and input_field.is_enabled():
                        input_field.clear()
                        input_field.send_keys("4")
                        time.sleep(random.uniform(1, constants.botSpeed))

                select_dropdowns = self.driver.find_elements(By.TAG_NAME, "select")
                for dropdown in select_dropdowns:
                    if dropdown.is_displayed() and dropdown.is_enabled():
                        select = Select(dropdown)
                        try:
                            select.select_by_visible_text('Yes')
                        except:
                            select.select_by_index(0)
                        time.sleep(random.uniform(1, constants.botSpeed))
                time.sleep(random.uniform(1, constants.botSpeed))
                self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']").click()

        except Exception as e:
            utils.prRed(f"❌ Error filling out additional questions: {str(e)}")

    def linkJobApply(self):
        self.generateUrls()
        countApplied = 0
        countJobs = 0

        urlData = utils.getUrlDataFile()

        for url in urlData:

            # todo: change the flow - next, nect, review, submit, if it needs additional questions check, do not rely on exceptions for core logic
            print(url)
            self.driver.get(url)
            time.sleep(random.uniform(1, constants.botSpeed))

            totalJobs = self.driver.find_element(By.XPATH, '//small').text
            totalPages = utils.jobsToPages(totalJobs)

            urlWords = utils.urlToKeywords(url)
            lineToWrite = "\n Category: " + urlWords[0] + ", Location: " + urlWords[1] + ", Applying " + str(
                totalJobs) + " jobs."
            self.displayWriteResults(lineToWrite)
            self.save_applied_jobs()

            for page in range(totalPages):

                currentPageJobs = constants.jobsPerPage * page
                url = url + "&start=" + str(currentPageJobs)
                self.driver.get(url)
                time.sleep(random.uniform(1, constants.botSpeed))

                offersPerPage = self.driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')
                offerIds = [(offer.get_attribute(
                    "data-occludable-job-id").split(":")[-1]) for offer in offersPerPage]
                time.sleep(random.uniform(1, constants.botSpeed))

                for offer in offersPerPage:
                    if not self.element_exists(offer, By.XPATH, ".//*[contains(text(), 'Applied')]"):
                        offerId = offer.get_attribute("data-occludable-job-id")
                        offerIds.append(int(offerId.split(":")[-1]))

                offerIds = [str(x) for x in offerIds]
                offerIds = list(set(offerIds) - self.already_applied)
                utils.prGreen(f"Only applying to {len(offerIds)}, rest already applied to")
                for jobID in offerIds:
                    offerPage = 'https://www.linkedin.com/jobs/view/' + str(jobID)
                    try:
                        self.driver.get(offerPage)
                        time.sleep(random.uniform(1, constants.botSpeed))

                        countJobs += 1

                        jobProperties = self.getJobProperties(countJobs)
                        if ("blacklisted" in jobProperties) or (jobID in self.already_applied):
                            lineToWrite = jobProperties + " | " + "* 🤬 Blacklisted Job, skipped!: " + str(offerPage)
                            self.displayWriteResults(lineToWrite)

                        else:
                            easyApplybutton = self.easyApplyButton()
                            print(f"Ready to apply to {jobID}")

                            if easyApplybutton is not False:
                                easyApplybutton.click()
                                time.sleep(random.uniform(1, constants.botSpeed))

                                try:
                                    print(f"Trying Resume and submit {jobID}")
                                    self.chooseResume()
                                    # need an exception here if it doesnt get triggered so  not using the method
                                    self.driver.find_element(By.CSS_SELECTOR,
                                                             f"button[aria-label='Submit Application']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))

                                    self.already_applied.add(str(jobID))
                                    lineToWrite = jobProperties + " | " + "* 🥳 Just Applied to this job: " + str(
                                        offerPage)
                                    self.displayWriteResults(lineToWrite)
                                    countApplied += 1

                                except:
                                    print("Need more info")
                                    try:
                                        self.driver.find_element(By.CSS_SELECTOR,
                                                                 f"button[aria-label='Continue to next step']").click()
                                        # press next, read percentage Num, see if it eiter asks for resume or for additional questions, and then keep going next
                                        comPercentage = self.driver.find_element(By.XPATH,
                                                                                 '/html/body/div[4]/div/div/div[2]/div/div[1]/span').text
                                        # comPercentage = self.driver.find_element(By.XPATH, '//*[@id="ember115"]/div/div[1]/span').text
                                        percenNumber = int(comPercentage[0:comPercentage.index("%")])

                                        time.sleep(random.uniform(1, constants.botSpeed))
                                        result = self.applyProcess(percenNumber, offerPage, jobID)

                                        lineToWrite = jobProperties + " | " + result
                                        self.displayWriteResults(lineToWrite)

                                    except Exception:
                                        self.chooseResume()
                                        self.driver.find_element(By.CSS_SELECTOR,
                                                                 f"button[aria-label={'Submit application'}]").click()
                                        lineToWrite = jobProperties + " | " + "* 🥵 Cannot apply to this Job! " + str(
                                            offerPage)
                                        self.displayWriteResults(lineToWrite)
                            else:
                                lineToWrite = jobProperties + " | " + "* 🥳 Already applied! Job: " + str(offerPage)
                                self.already_applied.add(str(jobID))
                                self.displayWriteResults(lineToWrite)
                    except Exception as e:
                        lineToWrite = "* 🥵 Cannot apply to this Job! Major Error " + str(
                            offerPage)
                        self.save_applied_jobs()
                        self.displayWriteResults(lineToWrite)

            utils.prYellow("Category: " + urlWords[0] + "," + urlWords[1] + " applied: " + str(countApplied) +
                           " jobs out of " + str(countJobs) + ".")

    def chooseResume(self):
        try:
            resume_page = self.driver.find_element(
                By.CLASS_NAME, "jobs-document-upload__title--is-required")
            if resume_page:
                resumes = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'ui-attachment--pdf')]")
                if (len(resumes) == 1 and resumes[0].get_attribute("aria-label") == "Select this resume"):
                    resumes[0].click()
                elif (len(resumes) > 1 and resumes[config.preferredCv - 1].get_attribute(
                        "aria-label") == "Select this resume"):
                    resumes[config.preferredCv - 1].click()
                elif (type(len(resumes)) != int):
                    utils.prRed(
                        "❌ No resume has been selected please add at least one resume to your Linkedin account.")
        except:
            pass

    def getJobProperties(self, count):
        textToWrite = ""
        jobTitle = ""
        jobLocation = ""

        try:
            jobTitle = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'job-title')]").get_attribute(
                "innerHTML").strip()
            res = [blItem for blItem in config.blackListTitles if (blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobTitle += "(blacklisted title: " + ' '.join(res) + ")"
        except Exception as e:
            if (config.displayWarnings):
                utils.prYellow("⚠️ Warning in getting jobTitle: " + str(e)[0:50])
            jobTitle = ""

        try:
            time.sleep(5)
            jobDetail = self.driver.find_element(By.XPATH,
                                                 "//div[contains(@class, 'job-details-jobs')]//div").text.replace("·",
                                                                                                                  "|")
            res = [blItem for blItem in config.blacklistCompanies if (blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobDetail += "(blacklisted company: " + ' '.join(res) + ")"
        except Exception as e:
            if (config.displayWarnings):
                print(e)
                utils.prYellow("⚠️ Warning in getting jobDetail: " + str(e)[0:100])
            jobDetail = ""

        try:
            jobWorkStatusSpans = self.driver.find_elements(By.XPATH,
                                                           "//span[contains(@class,'ui-label ui-label--accent-3 text-body-small')]//span[contains(@aria-hidden,'true')]")
            for span in jobWorkStatusSpans:
                jobLocation = jobLocation + " | " + span.text

        except Exception as e:
            if (config.displayWarnings):
                print(e)
                utils.prYellow("⚠️ Warning in getting jobLocation: " + str(e)[0:100])
            jobLocation = ""

        textToWrite = str(count) + " | " + jobTitle + " | " + jobDetail + jobLocation
        return textToWrite

    def easyApplyButton(self):
        try:
            time.sleep(random.uniform(1, constants.botSpeed))
            button = self.driver.find_element(By.XPATH,
                                              "//div[contains(@class,'jobs-apply-button--top-card')]//button[contains(@class, 'jobs-apply-button')]")
            EasyApplyButton = button
        except:
            EasyApplyButton = False

        return EasyApplyButton

    def applyProcess(self, percentage, offerPage, jobId):
        applyPages = math.floor(100 / percentage) - 2
        result = ""
        for pages in range(applyPages):
            # its not exactly working but if there are pre entered valus, seem to fine, need be
            self.fill_out_additional_questions()

            self.chooseResume()
            time.sleep(random.uniform(1, constants.botSpeed))
            # add resume bit here
            self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']").click()

        self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Review your application']").click()
        time.sleep(random.uniform(5, constants.botSpeed))

        if config.followCompanies is False:
            try:
                self.driver.find_element(By.CSS_SELECTOR, "label[for='follow-company-checkbox']").click()
            except:
                pass

        self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
        time.sleep(random.uniform(2, constants.botSpeed))

        result = "* 🥳 Just Applied to this job: " + str(offerPage)
        print("Adding to applied list")
        self.already_applied.add(str(jobId))

        return result

    def displayWriteResults(self, lineToWrite: str):
        try:
            print(lineToWrite)
            utils.writeResults(lineToWrite)
        except Exception as e:
            utils.prRed("❌ Error in DisplayWriteResults: " + str(e))

    def element_exists(self, parent, by, selector):
        return len(parent.find_elements(by, selector)) > 0

    def save_applied_jobs(self):
        """Save the set of applied jobs to a JSON file"""
        if not os.path.exists('data'):
            os.makedirs('data')
        with open(self.applied_jobs_file, 'w') as f:
            json.dump(list(self.already_applied), f)
        utils.prGreen(f"Saved {len(self.already_applied)} applied jobs to {self.applied_jobs_file}")


if __name__ == "__main__":
    start = time.time()
    bot = Linkedin()
    try:
        bot.linkJobApply()
    finally:
        bot.save_applied_jobs()
        end = time.time()
        utils.prYellow("---Took: " + str(round((time.time() - start) / 60)) + " minute(s).")
