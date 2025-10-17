import os

msg = os.getenv('APP_MESSAGE', 'Hello from Docker')
print(msg)
