almostalwaysup
==============

a multi-threaded python website healthchecker that dumps it's results into a postgresql database.

author: Tony Welder
email: tony.wvoip@gmail.com



Description
-----

I orginally wrote this python healthchecker to monitor the top one million websites, store the results into a postgresql database, and then display it on a pretty looking website with graphs(probably highcharts).  Turns out, you shouldn't use 8.8.8.8 as your primary DNS when running this application because google will block you like a crazy ex on facebook.

TODO
----
- Fix a serious bug associated with threads dying(daemon requires that you kick it)
- installation script that would install the database, the init script that doesn't exist, all of the python libs this little girl requires.
- Set up a website for yinz to the consume the data
- far better documentation... seriously 
