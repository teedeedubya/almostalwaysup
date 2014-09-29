# wrote by Tony Welder
# tony.wvoip@gmail.com
# description = I'm awesome

import time             #to track response time
import threading        #to spawn python threads
import Queue            #for creating queues to pass information between threads
import requests         #for pulling down webpages
import math             #not sure yet
import psycopg2         #for interacting with postgresql
import sys              #not sure
import pprint		#for printing out arrays
import logging		#for logging dipshit
import configuration    #global c for almostalwaysup

##########TO DO#################################
## associative arrays from postgresql queries ##
## add configurable start index               ##
## max allowd queue sizes                     ##
################################################

## global variables ##
c = configuration.Configuration()

class Master(threading.Thread):
## Master Thread
## in charge of creating working threads
## recreating worker threads when they fail
## pulling websites to be checked from database
## bulk inserting results of checks   
    def __init__(self, website_queue, result_queue,configuration):
        threading.Thread.__init__(self)
        self.website_queue = website_queue
        self.result_queue = result_queue
        self.c = configuration
        self.con = psycopg2.connect(database=self.c.database_name, \
            user=self.c.database_user, password=self.c.database_password,\
            host=self.c.database_host)

    def pull_websites(self, start_index):
        if (start_index + self.c.number_of_rows_per_pull) >= self.c.max_index:
            self.end_index = self.c.max_index
            self.index = 1
            self.current_run_finished = True

        else:
            self.end_index = start_index + self.c.number_of_rows_per_pull 
            self.index = self.end_index + 1

        self.cur = self.con.cursor()
        self.cur.execute('SELECT url_id, url, check_type FROM urls WHERE active = true \
                          AND url_id BETWEEN %s AND %s', (start_index, self.end_index))
        return self.cur.fetchall()

    def batch_insert(self):
    ## should probably move this function to be its own thread
        if self.result_queue.qsize() >= self.c.batch_insert:
            while self.result_queue.qsize() > self.c.batch_insert:
                self.to_be_inserted = []
                while len(self.to_be_inserted) <= self.c.batch_insert:
                    self.to_be_inserted.append(self.result_queue.get())
                    self.result_queue.task_done()                 
       
                self.args_str = ','.join(self.cur.mogrify("(%s,%s,%s,now())", x) for x in self.to_be_inserted)
                self.cur.execute("INSERT INTO checks (url_id, time_taken, response_size, date) values" + self.args_str)
                self.con.commit()

    def epoch_in_ms(self):
        return time.time() * 1000 

    def run(self):
        logging.info('Master thread %s started ' + self.name) 
        self.index = 1
        self.next_run = int(time.time()) + (self.c.check_interval_minutes * 60)
        self.current_run_finished = False
        self.debug_counter = 0
        self.debug_thread_time = 0
        self.debug_select_time = 0 
        self.debug_insert_time = 0

        while True:
            self.thread_time_start = self.epoch_in_ms() 
            if (threading.activeCount() - 2) < self.c.max_worker_threads:
                workers = []
                for i in range(self.c.max_worker_threads - (threading.activeCount() - 2)):
                    workers.append(Worker(self.website_queue, self.result_queue,c))
                for worker in workers:
                    worker.start()
            self.debug_thread_time += self.epoch_in_ms() - self.thread_time_start


            self.select_time_start = self.epoch_in_ms() 
            if self.current_run_finished is False:
                if self.website_queue.qsize() <= self.c.queue_size_before_batch_pull:
                    self.urls = self.pull_websites(self.index)
                    for self.url in self.urls:
                        self.website_queue.put(self.url)
            self.debug_select_time += self.epoch_in_ms() - self.select_time_start

            if self.current_run_finished is True and int(time.time()) > self.next_run:
                self.current_run_finished = False
                self.next_run = int(time.time()) + (self.c.check_interval_minutes * 60)
            
            self.insert_time_start = self.epoch_in_ms() 
            self.batch_insert()
            self.debug_insert_time += self.epoch_in_ms() - self.insert_time_start 
            if self.debug_counter % 10 == 0:
                logging.debug('current debug counter %s , current result queue %s, current website queue %s,' +\
                       'current timestamp %s, current run complete = %s, current index %s' +\
                       'next run timestamp %s, thread count %s, thread time %s, select time %s, insert time %s',\
                       self.debug_counter, self.result_queue.qsize(), self.website_queue.qsize(), time.time(),\
                       self.current_run_finished, self.index, self.next_run, threading.activeCount(),\
                       self.debug_thread_time, self.debug_select_time, self.debug_insert_time)             

            self.debug_counter += 1           
            time.sleep(1)

class Worker(threading.Thread):
##Worker Thread
##incharge of performing check
##calculating the amount of time taken and size of webpage
##inserting result into result_queue when finished
    def __init__(self, website_queue, result_queue,configuration):
        threading.Thread.__init__(self)
        self.website_queue = website_queue
        self.result_queue = result_queue
        self.c = configuration

    def is_within_tolerance(self, time_taken):
        if time_taken > self.c.max_milliseconds_to_wait:
            return False
        else:
            return True

    def protocol(self, check_type):
        if check_type == 1:
            return "http://"
        elif check_type == 2:
            return "https://"
        else:
            return "http://"

    def run(self):
        logging.info('Worker thread %s started ' + self.name) 

        while True:
            self.website = self.website_queue.get()
            self.url_id = self.website[0]
            self.url = self.website[1]
            self.check_type = self.website[2]
            self.attempt = 0
            self.status_code = 0

            while (self.attempt < self.c.max_attempts and self.status_code != 200):
                try:
                    self.attempt += 1
                    self.start_time = time.time() * 1000
                    self.r = requests.get(self.protocol(self.check_type) + self.url)
                    self.end_time = time.time() * 1000
                    self.status_code = self.r.status_code
                    if self.is_within_tolerance((self.end_time - self.start_time)) is False:
                        logging.error(self.url + 'fell outside of tolerance' )
                        self.status_code = 0
                except requests.exceptions.Timeout:
                    # Maybe set up for a retry, or continue in a retry loop
                    logging.error(self.url + 'Timed Out!')
                    print '%s timedout!' % self.url    
                except requests.exceptions.TooManyRedirects:
                    # Tell the user their URL was bad and try a different one
                    logging.error(self.url + 'too many redirects')
                except requests.exceptions.RequestException as e:
                    logging.error('Unknown Failure URL' + self.url + 'failed: ') 
                    print e
            if self.status_code == 0:
                #failure
                self.result_queue.put([self.url_id, 0, 0])

            else:
                #success
                self.result_queue.put([self.url_id, round((self.end_time - self.start_time ),2),len(self.r.text)])
            self.website_queue.task_done()
            time.sleep(0.25)

def main():
    logging.basicConfig(filename=c.log_file, level=c.log_level)
    logging.info('Almostalwaysup healthchecker daemon started!')
    website_queue = Queue.Queue()
    result_queue = Queue.Queue()
    master = Master(website_queue, result_queue,c)
    master.start()

if __name__ == '__main__':
    main()

