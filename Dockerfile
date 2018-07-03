from tiangolo/uwsgi-nginx-flask:python3.6

# Remove tiangolo's sample app
RUN rm -rf /app/*

WORKDIR /app

RUN mkdir /app/patternfinder
RUN mkdir /app/app

# Directories
ADD ./music_files /app/patternfinder/music_files
ADD ./patternfinder /app/patternfinder/patternfinder
ADD ./webapp/static /app/static
ADD ./webapp/templates /app/app/templates

# Files
ADD ./Makefile /app/patternfinder/
ADD ./setup.py /app/patternfinder/
ADD ./requirements.txt /app/patternfinder/
ADD ./webapp/requirements.txt /app/app/
ADD ./webapp/main.py /app/app/
ADD ./webapp/dpwc.py /app/app/
ADD ./webapp/uwsgi.ini /app/

RUN pip install -r /app/patternfinder/requirements.txt
RUN pip install -r /app/app/requirements.txt
RUN pip install /app/patternfinder/

EXPOSE 80

#ENV FLASK_APP=app/search.py

#CMD ["flask", "run", "--host=0.0.0.0", "--debugger", "--reload"]

#CMD ["python", "app/search.py"]

#CMD service nginx restart & uwsgi --ini patternfinder.ini --mount /patternfinder=app.search:application --gid www-data
