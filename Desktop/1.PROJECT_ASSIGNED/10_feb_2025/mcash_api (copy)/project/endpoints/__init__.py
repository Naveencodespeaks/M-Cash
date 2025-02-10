from fastapi import APIRouter, Body, Depends, Form
from project.common.utility import Utility
from project.constant.status_constant import SUCCESS, FAIL, WEB_URL, API_URL,EXCEPTION ,INTERNAL_ERROR,BAD_REQUEST,BUSINESS_LOGIG_ERROR
from fastapi import Depends
from sqlalchemy.orm import Session
from project.database.database import get_database_session
from project.common.auth import AuthHandler