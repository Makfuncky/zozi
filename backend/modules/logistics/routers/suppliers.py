"""Logistics suppliers router — consolidated from 0 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/logistics/suppliers", tags=["logistics", "suppliers"])
