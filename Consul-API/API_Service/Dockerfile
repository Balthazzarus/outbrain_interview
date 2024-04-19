FROM python:3
WORKDIR /usr/src/app
COPY python_dependancies.txt ./
RUN pip install --no-cache-dir -r python_dependancies.txt
COPY main.py ./
EXPOSE 8000
CMD [ "python", "-u", "./main.py" ]
