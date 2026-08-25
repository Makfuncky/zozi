"""Customer suppliers router — consolidated from 0 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/customer/suppliers", tags=["customer", "suppliers"])
