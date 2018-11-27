FROM    python
LABEL   maintainer="Sawood Alam <@ibnesayeed>"

ENV     PYTHONUNBUFFERED=1

WORKDIR /app
COPY    requirements.txt ./
RUN     pip install -r requirements.txt
COPY    . ./
RUN     chmod a+x *.py

CMD     ["./main.py"]
