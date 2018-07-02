from tiangolo/uwsgi-nginx-flask:python3.6

WORKDIR /PatternFinder

ADD ./setup.py /PatternFinder
ADD ./patternfinder /PatternFinder/patternfinder
ADD ./requirements.txt /PatternFinder/requirements.txt
ADD ./music_files /PatternFinder/music_files
ADD ./app /PatternFinder/app
ADD ./patternfinder.ini /PatternFinder/patternfinder.ini
ADD ./patternfinder.conf /etc/nginx/conf.d/patternfinder.conf
ADD ./wsgi.py /PatternFinder/wsgi.py

RUN pip install -r requirements.txt
RUN pip install -r app/requirements.txt
RUN pip install ./

EXPOSE 80

ENV FLASK_APP=app/search.py

#CMD ["flask", "run", "--host=0.0.0.0", "--debugger", "--reload"]

#CMD ["python", "app/search.py"]

CMD ["uwsgi", "--ini", "patternfinder.ini", "--mount", "/patternfinder=app.search:application", "--gid", "www-data"]
