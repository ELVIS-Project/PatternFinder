from tiangolo/uwsgi-nginx-flask:python3.6

WORKDIR /PatternFinder

ADD ./setup.py /PatternFinder
ADD ./patternfinder /PatternFinder/patternfinder
ADD ./music_files /PatternFinder/music_files
ADD ./app /PatternFinder/app
ADD ./requirements.txt /PatternFinder/requirements.txt
ADD ./patternfinder.ini /PatternFinder/patternfinder.ini

RUN pip install -r requirements.txt
RUN pip install -r app/requirements.txt
RUN pip install ./

EXPOSE 80

ENV FLASK_APP=app/search.py

#CMD ["flask", "run", "--host=0.0.0.0", "--debugger", "--reload"]

#CMD ["python", "app/search.py"]

CMD ["uwgsi", "--ini", "patternfinder.ini"]
