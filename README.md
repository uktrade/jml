# jml
Joiners Movers Leavers



## Local set up -> with out docker  
 pipenv install -r requirements.txt

## Added some exports for local set up

export SECRET_KEY=test_key-praveen
export ALLOWED_HOSTS=localhost,localhost:8000
export DATABASE_URL=psql://postgres:postgres@localhost:5432/EmployeeDB

chcked more env. variables from  'local.env.example'

## Start app using command below 

python manage.py runserver