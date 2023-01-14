#!/usr/bin/env python3

import sys
import os
from config import urls
import requests
from threading import Thread

def print_green(string):
    print('\x1B[32m' + str(string) + '\x1B[0m', end = '')

def print_red(string):
    print('\x1B[31m' + str(string) + '\x1B[0m', end = '')

def get(url):
    global get_response
    get_response = requests.get(url)

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

        self.http_success = 200 <= (self.http_response.status_code if self.http_response is not None else 0)< 300
        self.https_success = 200 <= (self.https_response.status_code if self.https_response is not None else 0)< 300
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

class Sites:
    def __init__(self, urls):
        self.failures = []
        self.sites = map(Site, urls)

    def test(self):
        for site in self.sites:
            site.test()

            if not site.success:
                self.failures.append(site)

    def summary(self):
        if len(self.failures) == 0:
            print('--- SUCCESS ---')
        else:
            print('--- FAILURE SUMMARY: ' + str(len(self.failures)) + ' FAILURE' + ('' if len(self.failures) == 1 else 'S') + ' ---')
            for site in self.failures:
                print(site)

    def success(self):
        return len(self.failures) == 0

def main():
    sites = Sites(urls)
    sites.test()
    print()
    sites.summary()

    os._exit(1 if not sites.success() else 0)

if __name__ == '__main__':
    main()
