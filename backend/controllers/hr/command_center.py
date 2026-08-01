import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from dependencies.db import get_db
from models import TreasuryAccount