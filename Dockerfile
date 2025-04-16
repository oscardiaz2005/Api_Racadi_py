FROM python:3.12.2
#set the working directory in he container
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8881

CMD ["uvicorn", "api.main:app" , "--host" ,  "0.0.0.0"  , "--port", "8000" , "--reload"]

