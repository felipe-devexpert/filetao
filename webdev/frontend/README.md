# Django Frontend Example.

To run and host your own Django server using this template there's only a few things you'll need;

Follow [this](https://github.com/ifrit98/storage-subnet/tree/webdev-metadata?tab=readme-ov-file#install-redis) information on how to set up Redis if you've not already done so.

Inside the webdev folder, run the command `python -m pip install -r requirements.txt`

Then run the FastAPI server by using `uvicorn main:app --host 127.0.0.1 --port 8000`.
You can add `--reload` if you're going to be making modifications to any of the FastApi code. Modify the IP in the command as nessecary.

To run the Django server, use this command while inside the webdev frontend folder (make sure it's the folder that contains `manage.py`) 
`python manage.py runserver 127.0.0.1:8080`
Replace the IP with anything you'd like.

Within the `views.py` file contained in the folder filetao, change the IP address to connect to the FastAPI server as needed.

Connect to the IP specified in the Django server command within a web broswer & enjoy.
