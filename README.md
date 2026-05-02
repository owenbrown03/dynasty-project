started with a to do list
then wanted to change all my fantasy football ideas and speradsheets into one website
started with the basics of just trying to pull all my leagues and store them in database

first issues:
-typos
-incorrect type formats
-learning about relationships and foreign keys, trying to set up my future indexing better
-nested jsons that sleeper api was returning, how to deal with those
-1-to-many vs 1-to-1, if sleeper randomly decides to nest a json where the league settings are nested in a settings object, we should just unwrap that on the spot rather than trying to store it like that to make it easier to use the database in the future, vs 1-to-many lets just make a whole nother table for that and establish a relationship
-tables will become complicated and needing to manage many relationships later to improve speed so we want to be learning ahead here to prepare
-when i was starting my env/docker fastapi was immediately crashing so i ran docker logs fastapi_app to find:
from . import models, crud, service
ImportError: attempted relative import with no known parent package

so when i was doing from . it was erroring because i was running main:app inside /app

-ran into some relationship issues due to misunderstanding of how it worked and what it was used for

my process was to make individual functions to make sure i had the process of sleeper -> database (just upsert in CRUD) down for each section (leagues, rosters, transactions) before moving into more of a cohesive unit

code started taking way too long so we need to start issuing some runtime improvements
lets start with asyncio

weaving though all the different relationships and stuff in my database seemed very overwhelming
but i was able to use my knowledge of data structs to make all the structs i needed up front so that i could use them easily later

i was also thinking pretty hard about which way i wanted to do things but finally decided to stop thinking and just time it and do it