#!/usr/bin/env python3

import sys
import os
import config
import requests
from threading import Thread
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import subprocess

def print_green(string):
    print('\x1B[32m' + str(string) + '\x1B[0m', end = '')

def print_red(string):
    print('\x1B[31m' + str(string) + '\x1B[0m', end = '')

def get(url):
    global get_response
    try:
        get_response = requests.get(url)
    except:
        get_response = None

def test_code(response):
    return 200 <= (response.status_code if response is not None else 0) < 300

def info(response):
    return str(response.status_code if response is not None else 'timeout')

def info_html(response):
    if response is not None:
        if test_code(response):
            return '<span style="color: green;">' + str(response.status_code) + '</span>'
        else:
            return '<span style="color: red;">' + str(response.status_code) + '</span>'
    else:
        return '<span style="color: red;">timeout</span>'

class Mailer:
    def __init__(self, mailer_config):
        self.config = mailer_config

    def send_mail(self, message):
        self.context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.config["host"], self.config["port"], context = self.context) as server:
            server.login(self.config["username"], self.config["password"])
            server.sendmail(self.config["username"], self.config["dest"], message.as_string())

class Site:
    def __init__(self, url):
        self.url = url
        self.http_response = None
        self.https_response = None
        self.http_success = None
        self.https_success = None
        self.success = None

    def __str__(self):
        return self.url

    def __unicode__(self):
        return self.__str__()

    def get(self, url):
        global get_response
        get_response = None
        thread = Thread(target = get, args = [url])
        thread.start()
        thread.join(timeout = 30)
        return get_response

    def test(self):
        print('[  ] ' + str(self) + '... ', end = '')
        sys.stdout.flush()
        self.http_response = self.get('http://' + self.url)
        self.https_response = self.get('https://' + self.url)

        self.http_success = test_code(self.http_response)
        self.https_success = test_code(self.https_response)
        self.success = self.http_success and self.https_success

        print('\r[', end = '')
        if self.success:
            print_green('OK')
        else:
            print_red('KO')

        print('] ' + str(self) + '   \b\b\b', end = '')

        if not self.success:
            errors = []
            if not self.http_success:
                errors.append('http server returned ' + info(self.http_response))

            if not self.https_success:
                errors.append('https server returned ' + info(self.https_response))

            print_red(' ' + ', '.join(errors) +'\n')

        else:
            print()

class Tester:
    def __init__(self, mailer_config, urls):
        self.failures = []
        self.mailer = Mailer(mailer_config)
        self.sites = list(map(Site, urls))

    def test(self):
        for site in self.sites:
            site.test()

            if not site.success:
                self.failures.append(site)

    def summary(self):
        if len(self.failures) == 0:
            return '--- SUCCESS ---'
        else:
            content = '--- FAILURE SUMMARY: ' + str(len(self.failures)) + ' FAILURE' + ('' if len(self.failures) == 1 else 'S') + ' ---\n'
            for site in self.failures:
                content += '- ' + site.url + '\n'
            return content

    def summary_html(self):
        if len(self.failures) == 0:
            return '<h2>Uptest passed correctly.</h2>'
        else:
            content = '<h2>There ' + ('was ' if len(self.failures) == 1 else 'were ')
            content += str(len(self.failures)) + ' failure' + ('' if len(self.failures) == 1 else 's')
            content += ' during the uptest.</h2>\n'
            content += '<p><ul>\n'
            for site in self.failures:

                if not test_code(site.http_response) and test_code(site.https_response):
                    content += '<li><a href="http://' + site.url + '">http://' + site.url + '</a> returned '
                    content += info(site.http_response) + ' for HTTP.</li>\n'

                if not test_code(site.https_response) and test_code(site.http_response):
                    content += '<li><a href="https://' + site.url + '">https://' + site.url + '</a> returned '
                    content += info(site.https_response) + ' for HTTPS.</li>\n'

                if not test_code(site.https_response) and not test_code(site.http_response):
                    content += '<li><a href="https://' + site.url + '">https://' + site.url + '</a> returned '
                    content += info(site.http_response) + ' for HTTP and '
                    content += (info(site.https_response) + ' for') if info(site.http_response) != info(site.https_response) else ''
                    content += ' HTTPS.</li>\n'

            content += '</ul></p>\n'

            content += '<h2>Details</h2>\n'
            content += '<p><table style="border-collapse: collapse;">\n'
            content += '<tr style="border-bottom: 2px solid;">'
            content += '<th style="padding: 10px;">Page</th>'
            content += '<th style="padding: 10px;">HTTP</th>'
            content += '<th style="padding: 10px;">HTTPS</th>'
            content += '</tr>\n'

            for site in self.sites:
                content += '<tr style="border-bottom: 1px solid;">'
                content += '<td style="padding: 10px;"><a href="https://' + site.url + '">' + site.url + '</td>'
                content += '<td style="padding: 10px;">' + info_html(site.http_response) + '</td>'
                content += '<td style="padding: 10px;">' + info_html(site.https_response) + '</td>'
                content += '</tr>\n'

            content += '</table></p>\n'

            return content

    def notify(self):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Error occured in uptest"
        msg['From'] = self.mailer.config["username"]
        msg['To'] = self.mailer.config["dest"]
        msg.attach(MIMEText(self.summary(), 'plain'))
        msg.attach(MIMEText(self.summary_html(), 'html'))
        self.mailer.send_mail(msg)

    def success(self):
        return len(self.failures) == 0

def download_s3(key):
    subprocess.call(
        ["aws", "--endpoint-url", config.s3.get("endpoint"), "s3", "cp", "s3://" + config.s3.get("bucket") + "/uptest/" + key, '.'],
        env = {
            "AWS_ACCESS_KEY_ID": config.s3.get("key"),
            "AWS_SECRET_ACCESS_KEY": config.s3.get("secret"),
            "AWS_DEFAULT_REGION": config.s3.get("region"),
            "AWS_DEFAULT_REGION": config.s3.get("region"),
        }
    )

def upload_s3(key):
    subprocess.call(
        ["aws", "--endpoint-url", config.s3.get("endpoint"), "s3", "cp", key, "s3://" + config.s3.get("bucket") + "/uptest/" + key],
        env = {
            "AWS_ACCESS_KEY_ID": config.s3.get("key"),
            "AWS_SECRET_ACCESS_KEY": config.s3.get("secret"),
            "AWS_DEFAULT_REGION": config.s3.get("region"),
            "AWS_DEFAULT_REGION": config.s3.get("region"),
        }
    )

def main():

    oneshot = len(sys.argv) > 1 and sys.argv[1] == "--one-shot"

    if not oneshot:
        # Failed once indicate that we had an error last time, but we want the error to happen twice before notifying, so if
        # we have an error that occurs again, we will need to notify.
        failed_once = []

        # Failed twice means that they were already notified, so we don't need to notify again.
        failed_twice = []

        try:
            if config.s3:
                download_s3("failed_once.txt")
            with open('failed_once.txt', 'r') as f:
                failed_once = list(filter(lambda x: x != '', map(lambda x: x[0:-1], f)))

        except:
            pass

        try:
            if config.s3:
                download_s3("failed_twice.txt")
            with open('failed_twice.txt', 'r') as f:
                failed_twice = list(filter(lambda x: x != '', map(lambda x: x[0:-1], f)))
        except:
            pass

    tester = Tester(config.mailer, config.urls)
    tester.test()
    print()
    print(tester.summary())

    if oneshot:
        if len(tester.failures) > 0:
            tester.notify()

    else:
        new_failure = False
        new_failed_twice = []

        for failure in tester.failures:

            if failure.url in failed_once:

                # new_failed_twice contains everything that has failed at least twice
                new_failed_twice.append(failure.url)

                # It has failed once, and fails twice for the first time
                if not failure.url in failed_twice:

                    # We need to notify
                    new_failure=True

        if new_failure:
            tester.notify()

        with open('failed_once.txt', 'w') as f:
            f.write('\n'.join(map(lambda x: x.url, tester.failures)) + '\n')

        with open('failed_twice.txt', 'w') as f:
            f.write('\n'.join(new_failed_twice) + '\n')

        if config.s3:
            upload_s3("failed_once.txt")
            upload_s3("failed_twice.txt")



if __name__ == '__main__':
    main()
