
<p align="center">
    <h2>mrcash-api <h2>
</p>


  

## Technology Stack:
* Python version Python 3.12.5 or above
* FastAPI
* Uvicorn (server)
* Sqlalchemy
* MySql
* Alembic (database migrations)


## start the project ?
```
python -m venv env                  #create a virtual environment
.\env\Scripts\activate              #activate your virtual environment

poetry install  #if poerty instalized 
     Or Else
pip install -r requirements.txt
update your database connection string in .env
uvicorn application:app --reload    #start server use --host for host if required
visit Welcome screen at 127.0.0.1:8000 
visit Swagger UI docs screen at 127.0.0.1:8000/docs  # here all api routing and request can be triggered...

```

## Alembic Migrations for SqlAlchemy
```
* Install alembic
pip install alembic

step 1: cd project then 
step 2 Run command in terminal  `alembic init alembic` not required if already initstlized 
step 3: mention your mysql connection string inside sqlalchemy.url

step 4: in env.py file inside alembic dir mention all models inside target_metadata this way 
target_metadata = [user.Base.metadata, client.Base.metadata] (not Required)

step 5: alembic revision --autogenerate -m "message to identify migration"

step 6: now below command will migrate all changes to the database
step 7: alembic upgrade head

step 7: whenever you make changes into the models then create the revision and upgrade it, even if you remove fields from the models upgrade command will be used
alembic revision --autogenerate -m "second migration message"
followed by alembic upgrade first three or four initials of your recent version created in my case command was
alembic upgrade 2a43 

to downgrade the recent migration simply alembic downgrade first three or four initials of your recent version created in my case command was
alembic downgrade 2a43
```
