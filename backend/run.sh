#!/bin/bash
PYTHONPATH=. uvicorn src.app:app --host 0.0.0.0 --port 3001 --reload 