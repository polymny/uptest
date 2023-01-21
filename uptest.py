#!/usr/bin/env python3

import sys
import os
import config
import requests
from threading import Thread
import smtplib
import ssl

def print_green(string):
    print('\x1B[32m' + str(string) + '\x1B[0m', end = '')

def print_red(string):
    print('\x1B[31m' + str(string) + '\x1B[0m', end = '')

def get(url):
    global get_response
    get_response = requests.get(url)

class Mailer:
    def __init__(self, mailer_config):
        self.config = mailer_config

    def send_mail(self, message):
        self.context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.config["host"], self.config["port"], context = self.context) as server:
            server.login(self.config["username"], self.config["password"])
            server.sendmail(self.config["username"], self.config["dest"], message)

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
        thread.join(timeout = 5)
        return get_response

    def test(self):
        print('[  ] ' + str(self) + '... ', end = '')
        sys.stdout.flush()
        self.http_response = self.get('http://' + self.url)
        self.https_response = self.get('https://' + self.url)

        self.http_success = 200 <= (self.http_response.status_code if self.http_response is not None else 0) < 300
        self.https_success = 200 <= (self.https_response.status_code if self.https_response is not None else 0) < 300
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
                errors.append('http server returned ' + str(self.http_response.status_code if self.http_response is not None else 'timeout'))

            if not self.https_success:
                errors.append('https server returned ' + str(self.https_response.status_code if self.https_response is not None else 'timeout'))

            print_red(' ' + ', '.join(errors) +'\n')

        else:
            print()

class Tester:
    def __init__(self, mailer_config, urls):
        self.failures = []
        self.mailer = Mailer(mailer_config)
        self.sites = map(Site, urls)

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
                content += site.url.replace(".", "-") + '\n'
            return content

    def notify(self):
        self.mailer.send_mail("Subject: Errors occured in uptest\n\n" + self.summary())

    def success(self):
        return len(self.failures) == 0

def main():
    tester = Tester(config.mailer, config.urls)
    tester.test()
    print()
    print(tester.summary())

    if not tester.success():
        tester.notify()
        # os._exit(1)
    else:
        pass
        # os._exit(0)

if __name__ == '__main__':
    main()
