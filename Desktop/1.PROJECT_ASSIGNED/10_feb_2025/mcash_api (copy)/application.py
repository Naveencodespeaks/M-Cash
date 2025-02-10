from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from project.routes.api import router as api_router
from project.common.utility import Utility
from project.constant.status_constant import SUCCESS, FAIL
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import List, Dict, Any
from fastapi.responses import JSONResponse
import re
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime, timedelta
import os
from  project.aploger import AppLogger
# This way all the tables can be created in database but cannot be updated for that use alembic migrations
# user.Base.metadata.create_all(bind=engine)
logs_dir = "./logs/"  
days_back = 6
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    app = FastAPI(title="Mcash-App", description="Mcash",version="1.0", docs_url=None, redoc_url=None)
else:
    app = FastAPI(title="Mcash-App", description="Mcash",version="1.0")


# Custom error response format
def format_error_details(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    formatted_errors = {}
    for error in errors:
        loc = "->".join(str(i) for i in error["loc"])
        print(loc)
        loc = loc.replace("body->","")
        context = error.get("ctx", {})
        reason =context.get("reason",[])
        formatted_errors[str(loc)] = {
            "message": re.sub(re.escape("value error, "), '', error["msg"], flags=re.IGNORECASE) ,
            "input": error.get("input", ''),
            #"context": context, #error.get("ctx", {})
            "reason":str(reason)
        }
    return formatted_errors

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    formatted_errors = format_error_details(exc.errors())
    
    return JSONResponse({
        "status":422,
        "message":"Validation Error",
        "errors":formatted_errors,
        "code":"INPUT_VALIDATION_ERROR"

    },status_code=422)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
scheduler = BackgroundScheduler()

def delete_old_log_folders(log_folder: str, n_days: int):
       
        current_time = time.time()
        threshold_time = current_time - (n_days * 86400)
        for filename in os.listdir(log_folder):
            file_path = os.path.join(log_folder, filename)

            # Check if it's a file (not a directory)
            if os.path.isfile(file_path):
                file_mod_time = os.path.getmtime(file_path)
                if file_mod_time < threshold_time:
                    os.remove(file_path)
now = datetime.now()
next_run_time = now.replace(hour=1, minute=0, second=0, microsecond=0)
if now >= next_run_time:
    next_run_time += timedelta(days=1)
scheduler.add_job(delete_old_log_folders, 'interval', hours=24, next_run_time=next_run_time,args=[logs_dir, days_back])
scheduler.start()

          

@app.get("/")
def read_root():
    try:
        return Utility.json_response(status=SUCCESS, message="Welcome to M-Cash", error=[], data={})
    except Exception as E:
        AppLogger.error(str(E))
        return Utility.json_response(status=FAIL, message="Something went wrong", error=[], data={})


@app.get("/media/images/{image}")
def images( image: str):
    file_location = f"project/media/images/{image}"
    return FileResponse(file_location)

# if __name__ == '__main__':
#     uvicorn.run("application:app", host='localhost', port=8000, log_level="debug", reload=True)
#     print("running")
