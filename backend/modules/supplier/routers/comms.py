"""Supplier comms router — consolidated from 0 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/supplier/comms", tags=["supplier", "comms"])
