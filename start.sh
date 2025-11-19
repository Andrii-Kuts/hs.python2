docker build -t pesun-analysis .
docker run -v $(pwd)/cache:/app/cache -v $(pwd)/logs:/app/logs -p 8050:8050 -it pesun-analysis