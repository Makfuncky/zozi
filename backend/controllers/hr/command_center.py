import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from data.dependencies_db import get_db
from data.models import TreasuryAccount