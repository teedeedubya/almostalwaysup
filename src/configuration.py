import logging

class Configuration():
## configuration file for healthchecker.py
    def __init__(self):
       ##number of worker threads to pull websites and to perform health checks
       self.max_worker_threads = 500 

       ##maximum amount of time to wait before considering a website down
       self.max_milliseconds_to_wait = 15000

       ##maximum number of retries allowd before considering a website to be down
       self.max_attempts = 3

       ##the number of results in the "results_queue" before inserting them at 
       ##the same time into the postgresql database
       self.batch_insert = 40

       ##number of websites to pull per select select query against the database
       self.number_of_rows_per_pull = 400 

       ##how often to check should the websites be rechecked
       self.check_interval_minutes = 30

       ##the level the website_queue needs to be at before peforming a select 
       ##against to replenish the queue to perform more health checks
       self.queue_size_before_batch_pull = 0 

       ##the higher the number, the lower the ranking on alexa.  
       ##the higher you set this number, the more websites that will be check
       self.max_index = 50000 

       ##database name in the postgresql database
       self.database_name = 'almostalwaysup'

       ##postgresql username to connect with
       self.database_user = 'frodo'

       ##password to be used to connect to the postgresql database
       self.database_password = 'rainingmen'

       ##hostname, URL, or IP of the postgresql database
       self.database_host = 'db00'

       ##log file location, bear in mind this file needs be owned by the user 
       ##running this program.
       self.log_file = '/var/log/almostalwaysup.log'

       ##log level for the script to be set at
       ##log levels, DEBUG INFO WARNING ERROR CRITICAL
       self.log_level = logging.DEBUG

       ##directory for exchanging information of status of various threads
       ##SHOULD BE A RAM DISK!!!!
       self.ram_disk = '/ramdisk'
