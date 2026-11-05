#!/usr/bin/env bash
echo "==============================================================================="
echo "                TalentPulse AI Enterprise HR Management System"
echo "==============================================================================="
echo ""
echo "Select runtime option:"
echo "1) FastAPI Enterprise Server (Port 8000)"
echo "2) Standalone Unified Flask Server (Port 8000)"
echo "3) Install Dependencies"
echo "4) Run Test Suite"
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        cd backend && python -c "import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000)"
        ;;
    2)
        cd backend && python server.py
        ;;
    3)
        python -m pip install -r requirements.txt
        ;;
    4)
        cd backend && pytest tests/ -v
        ;;
    *)
        echo "Invalid selection"
        ;;
esac
