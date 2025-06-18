# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a food calorie analysis system that uses Vision Language Models (VLM) to analyze food images and calculate nutritional information. The system integrates with Notion as a frontend and provides a local Mac backend service for AI processing.

## Architecture

-   **VLM Service**: FastAPI server (`VLM/server.py`) running InternVL3 models for food image analysis
-   **Notion Integration**: Webhook-based integration for user input/output via Notion databases
-   **USDA API**: Food nutrition database lookup for accurate calorie calculations
-   **Translation Service**: Local translation between Chinese and English food names

## Development Commands

### Start VLM Server

```bash
cd VLM
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Start API Service (Recommended)

```bash
python api_service.py
```

This starts the comprehensive API service on port 8001 that integrates VLM analysis with USDA nutrition data.

### Start Frontend Server

```bash
cd frontend
python server.py
```

### Test Food Analysis (CLI)

```bash
python request_model.py
```

The test client allows you to choose between:
- VLM service only (port 8000) - image analysis only
- Comprehensive API service (port 8001) - image analysis + nutrition data

### Test USDA API

```bash
source ~/miniconda3/bin/activate torch
cd USDA
python test_api.py
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Key Components

### API Services

-   **VLM Server**: `VLM/server.py` provides basic image analysis at port 8000
-   **API Service**: `api_service.py` comprehensive service at port 8001 that:
    -   Integrates VLM analysis with USDA nutrition data
    -   Provides complete food analysis with calorie calculations
    -   Handles multiple data sources with fallback mechanisms
    -   Offers endpoints for both complete analysis and individual components

### VLM Models

-   **Primary**: InternVL3-2B model with optimizations for MPS/CUDA
-   **Location**: `VLM/InternVL3.py` contains the model loading and inference logic
-   **Server**: `VLM/server.py` provides REST API endpoint at `/analyze`
-   **Prompt**: Food analysis prompt template in `VLM/prompts/food_prompt.txt`

### API Integration

-   **USDA FoodData Central**: 
    -   `USDA/test_api.py`: Core API client with comprehensive nutrition lookup
    -   `USDA/usda_service.py`: Integration service for VLM results with fallback estimation
-   **Notion API**: `notion/notion.py` for webhook handling and database operations
-   **Translation**: `text/local.py` for Chinese-English food name translation

### Performance Notes

-   Model loading includes 8-bit quantization and MPS optimization for Mac
-   `max_tiles` parameter controls memory usage (1=4GB, 4=8GB, 9=16GB VRAM)
-   Compilation optimization available for MPS backend

## Environment Setup

-   Requires PyTorch with MPS/CUDA support
-   NOTION_TOKEN environment variable needed for Notion integration
-   USDA API key required for nutritional data access
-   uses conda environment `torch` with necessary packages installed

## File Structure

-   `foods/`: Sample food images for testing
-   `VLM/`: Vision language model implementation and server
-   `frontend/`: Web-based user interface
    -   `index.html`: Main web interface
    -   `script.js`: Frontend logic and API integration
    -   `style.css`: Modern responsive styling
    -   `server.py`: Simple HTTP server for development
-   `notion/`: Notion API integration and webhook handling
-   `USDA/`: USDA nutrition database integration
-   `text/`: Translation utilities
-   `request_model.py`: Client for testing the VLM server

## Model Performance

InternVL3-2B typical inference times:

-   MPS (Mac): 12-27 seconds depending on tile configuration
-   CUDA: 7-18 seconds depending on GPU and tile configuration
-   Tile=1 for memory constrained environments, Tile=4 for balanced performance
