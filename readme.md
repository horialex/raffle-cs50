# CS50 final project: Raffle


To run the app run command in the root of the project

```bash
flask --app ./api/app run --debug
```



## database migrations
When you move the app to another system and want to spin up a new db - after you start the db container you need to run the following commands
to create the db schema

```bash
rm -rf migrations/

flask db init

flask db migrate -m "initial schema"

flask db upgrade
```
