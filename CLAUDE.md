# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a food calorie analysis system that uses Vision Language Models (VLM) to analyze food images and calculate nutritional information. The system integrates with Notion as a frontend and provides a local Mac backend service for AI processing.

## Architecture

- **VLM Service**: FastAPI server (`VLM/server.py`) running InternVL3 models for food image analysis
- **Notion Integration**: Webhook-based integration for user input/output via Notion databases
- **USDA API**: Food nutrition database lookup for accurate calorie calculations
- **Translation Service**: Local translation between Chinese and English food names

## Development Commands

### Start VLM Server
```bash
cd VLM
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Test Food Analysis
```bash
python request_model.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Key Components

### VLM Models
- **Primary**: InternVL3-2B model with optimizations for MPS/CUDA
- **Location**: `VLM/InternVL3.py` contains the model loading and inference logic
- **Server**: `VLM/server.py` provides REST API endpoint at `/analyze`
- **Prompt**: Food analysis prompt template in `VLM/prompts/food_prompt.txt`

### API Integration
- **USDA FoodData Central**: `USDA/test_api.py` for nutritional data lookup
- **Notion API**: `notion/notion.py` for webhook handling and database operations
- **Translation**: `text/local.py` for Chinese-English food name translation

### Performance Notes
- Model loading includes 8-bit quantization and MPS optimization for Mac
- `max_tiles` parameter controls memory usage (1=4GB, 4=8GB, 9=16GB VRAM)
- Compilation optimization available for MPS backend

## Environment Setup

- Requires PyTorch with MPS/CUDA support
- NOTION_TOKEN environment variable needed for Notion integration
- USDA API key required for nutritional data access

## File Structure

- `foods/`: Sample food images for testing
- `VLM/`: Vision language model implementation and server
- `notion/`: Notion API integration and webhook handling
- `USDA/`: USDA nutrition database integration
- `text/`: Translation utilities
- `request_model.py`: Client for testing the VLM server

## Model Performance

InternVL3-2B typical inference times:
- MPS (Mac): 12-27 seconds depending on tile configuration
- CUDA: 7-18 seconds depending on GPU and tile configuration
- Tile=1 for memory constrained environments, Tile=4 for balanced performance