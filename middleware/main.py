import uvicorn
from fastapi import FastAPI  


mymiddleware=FastAPI()



if __init__ == '__main__':
    uvicorn.run(
        host="0.0.0.0",
        port=8400,
        app=mymiddleware
    )