"""
Interactive Multi-Pivot Table Creator (Codex V5)
==============================================

A modern web application for creating and managing multiple pivot tables with advanced features:
- Modern, responsive UI optimized for both keyboard and mouse users
- Copy filters between pivots
- Persistent state management across sessions
- Advanced filtering with date operations
- Export capabilities (CSV, Python code)
- Real-time pivot updates

Backend: FastAPI (Python)
Frontend: Modern HTML/CSS/JavaScript
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import io
import traceback
from typing import List, Dict, Any, Optional
import uvicorn

app = FastAPI(title="Pivot Codex V5", description="Advanced Pivot Table Creator")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state management
class AppState:
    def __init__(self):
        self.dataframes = {}  # session_id: dataframe
        self.pivot_configs = {}  # session_id: list of pivot configs
        self.saved_views_file = "saved_pivot_views_v5.json"
        
    def get_session_data(self, session_id: str):
        if session_id not in self.dataframes:
            return None
        return self.dataframes[session_id]
    
    def set_session_data(self, session_id: str, df: pd.DataFrame):
        self.dataframes[session_id] = df
        if session_id not in self.pivot_configs:
            self.pivot_configs[session_id] = []
    
    def get_pivot_configs(self, session_id: str):
        return self.pivot_configs.get(session_id, [])
    
    def set_pivot_configs(self, session_id: str, configs: List[Dict]):
        self.pivot_configs[session_id] = configs
    
    def serialize_dates(self, obj):
        if isinstance(obj, dict):
            return {k: self.serialize_dates(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.serialize_dates(v) for v in obj]
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        return obj
    
    def save_views(self, session_id: str):
        try:
            configs = self.get_pivot_configs(session_id)
            # Remove non-serializable data
            clean_configs = []
            for config in configs:
                clean_config = {k: v for k, v in config.items() 
                              if k not in ['pivot_df', 'filtered_df']}
                clean_configs.append(self.serialize_dates(clean_config))
            
            with open(self.saved_views_file, 'w') as f:
                json.dump(clean_configs, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving views: {e}")
            return False
    
    def load_views(self, session_id: str):
        try:
            with open(self.saved_views_file, 'r') as f:
                loaded_configs = json.load(f)
                # Add missing fields
                for config in loaded_configs:
                    config['pivot_df'] = None
                    config['filtered_df'] = None
                    config['id'] = str(uuid.uuid4())
                self.set_pivot_configs(session_id, loaded_configs)
            return True
        except Exception as e:
            print(f"Error loading views: {e}")
            return False

state = AppState()

# Static files directory
static_dir = Path(__file__).parent.parent / "static"

# Utility functions
def default_pivot_config():
    return {
        'id': str(uuid.uuid4()),
        'name': f'Pivot {datetime.now().strftime("%H:%M:%S")}',
        'index_cols': [],
        'column_cols': [],
        'value_agg_list': [],
        'filters': [],
        'fill_value_enabled': False,
        'custom_fill_value': None,
        'margins_enabled': False,
        'margins_name': 'All_Totals',
        'pivot_df': None,
        'filtered_df': None,
        'generated_code': None,
        'error_log': '',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Process uploaded dataframe with date parsing and cleanup"""
    df_processed = df.copy()
    
    # Clean and convert date columns
    for col in df_processed.columns:
        if df_processed[col].dtype == object:
            # Replace invalid dates
            df_processed[col] = df_processed[col].replace("0000-00-00", pd.NA)
            # Try to convert to datetime
            try:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='ignore')
            except Exception:
                pass
    
    return df_processed

def apply_filters(df: pd.DataFrame, filters: List[Dict]) -> pd.DataFrame:
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    for f in filters:
        if not f.get('column') or not f.get('operator'):
            continue
            
        col = f['column']
        op = f['operator']
        value = f.get('value', '')
        
        if col not in filtered_df.columns:
            continue
            
        try:
            if op == '==':
                if pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
                    filtered_df = filtered_df[filtered_df[col] == pd.to_datetime(value)]
                else:
                    filtered_df = filtered_df[filtered_df[col] == value]
            elif op == '!=':
                if pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
                    filtered_df = filtered_df[filtered_df[col] != pd.to_datetime(value)]
                else:
                    filtered_df = filtered_df[filtered_df[col] != value]
            elif op == '>':
                if pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
                    filtered_df = filtered_df[filtered_df[col] > pd.to_datetime(value)]
                else:
                    filtered_df = filtered_df[filtered_df[col] > float(value)]
            elif op == '<':
                if pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
                    filtered_df = filtered_df[filtered_df[col] < pd.to_datetime(value)]
                else:
                    filtered_df = filtered_df[filtered_df[col] < float(value)]
            elif op == '>=':
                if pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
                    filtered_df = filtered_df[filtered_df[col] >= pd.to_datetime(value)]
                else:
                    filtered_df = filtered_df[filtered_df[col] >= float(value)]
            elif op == '<=':
                if pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
                    filtered_df = filtered_df[filtered_df[col] <= pd.to_datetime(value)]
                else:
                    filtered_df = filtered_df[filtered_df[col] <= float(value)]
            elif op == 'contains':
                filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(str(value), na=False)]
            elif op == 'not_contains':
                filtered_df = filtered_df[~filtered_df[col].astype(str).str.contains(str(value), na=False)]
            elif op == 'in':
                values = [v.strip() for v in str(value).split(',')]
                filtered_df = filtered_df[filtered_df[col].isin(values)]
            elif op == 'not_in':
                values = [v.strip() for v in str(value).split(',')]
                filtered_df = filtered_df[~filtered_df[col].isin(values)]
                
        except Exception as e:
            print(f"Error applying filter {f}: {e}")
            continue
    
    return filtered_df

def create_pivot_table(df: pd.DataFrame, config: Dict) -> Dict:
    """Create pivot table based on configuration"""
    try:
        # Apply filters first
        filtered_df = apply_filters(df, config.get('filters', []))
        
        if filtered_df.empty:
            return {
                'success': False,
                'error': 'No data after applying filters',
                'pivot_df': None,
                'filtered_df': filtered_df
            }
        
        # Prepare aggregation dictionary
        agg_dict = {}
        for item in config.get('value_agg_list', []):
            if item.get('value_col'):
                agg_dict[item['value_col']] = item.get('agg_func', 'sum')
        
        if not agg_dict:
            return {
                'success': False,
                'error': 'No value columns specified',
                'pivot_df': None,
                'filtered_df': filtered_df
            }
        
        # Create pivot table
        pivot_df = pd.pivot_table(
            filtered_df,
            values=list(agg_dict.keys()),
            index=config.get('index_cols', []) or None,
            columns=config.get('column_cols', []) or None,
            aggfunc=agg_dict,
            fill_value=config.get('custom_fill_value') if config.get('fill_value_enabled') else None,
            margins=config.get('margins_enabled', False),
            margins_name=config.get('margins_name', 'All_Totals')
        )
        
        return {
            'success': True,
            'pivot_df': pivot_df,
            'filtered_df': filtered_df,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'pivot_df': None,
            'filtered_df': None
        }

def generate_python_code(config: Dict) -> str:
    """Generate Python code for the pivot configuration"""
    code_lines = [
        "import pandas as pd",
        "",
        "# Load your data",
        "df = pd.read_csv('your_file.csv')",
        "",
        "# Process data (date parsing, etc.)",
        "for col in df.columns:",
        "    if df[col].dtype == object:",
        "        df[col] = df[col].replace('0000-00-00', pd.NA)",
        "        try:",
        "            df[col] = pd.to_datetime(df[col], errors='ignore')",
        "        except Exception:",
        "            pass",
        ""
    ]
    
    # Add filters
    if config.get('filters'):
        code_lines.append("# Apply filters")
        for f in config['filters']:
            if f.get('column') and f.get('operator') and f.get('value'):
                col = f['column']
                op = f['operator']
                value = f['value']
                
                if op == '==':
                    code_lines.append(f"df = df[df['{col}'] == '{value}']")
                elif op == '!=':
                    code_lines.append(f"df = df[df['{col}'] != '{value}']")
                elif op == 'contains':
                    code_lines.append(f"df = df[df['{col}'].str.contains('{value}', na=False)]")
                # Add more operators as needed
        code_lines.append("")
    
    # Add pivot table creation
    agg_dict = {}
    for item in config.get('value_agg_list', []):
        if item.get('value_col'):
            agg_dict[item['value_col']] = item.get('agg_func', 'sum')
    
    code_lines.extend([
        "# Create pivot table",
        "pivot_df = pd.pivot_table(",
        "    df,",
        f"    values={list(agg_dict.keys())},",
        f"    index={config.get('index_cols', [])},",
        f"    columns={config.get('column_cols', [])},",
        f"    aggfunc={agg_dict},",
        f"    fill_value={config.get('custom_fill_value') if config.get('fill_value_enabled') else None},",
        f"    margins={config.get('margins_enabled', False)},",
        f"    margins_name='{config.get('margins_name', 'All_Totals')}'",
        ")",
        "",
        "print(pivot_df)"
    ])
    
    return "\n".join(code_lines)

# API Routes
@app.get("/", response_class=HTMLResponse)
async def get_index():
    return FileResponse(str(static_dir / 'index.html'))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = "default"):
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        df_processed = process_dataframe(df)
        
        state.set_session_data(session_id, df_processed)
        
        return {
            'success': True,
            'filename': file.filename,
            'shape': df_processed.shape,
            'columns': df_processed.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df_processed.dtypes.items()}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/api/data/{session_id}")
async def get_data_info(session_id: str):
    df = state.get_session_data(session_id)
    if df is None:
        raise HTTPException(status_code=404, detail="No data found for session")
    
    return {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'sample_data': df.head().to_dict('records')
    }

@app.get("/api/pivots/{session_id}")
async def get_pivots(session_id: str):
    configs = state.get_pivot_configs(session_id)
    # Remove non-serializable data for API response
    clean_configs = []
    for config in configs:
        clean_config = {k: v for k, v in config.items() 
                      if k not in ['pivot_df', 'filtered_df']}
        clean_configs.append(clean_config)
    return clean_configs

@app.post("/api/pivots/{session_id}")
async def create_pivot(session_id: str):
    df = state.get_session_data(session_id)
    if df is None:
        raise HTTPException(status_code=404, detail="No data found for session")
    
    configs = state.get_pivot_configs(session_id)
    new_config = default_pivot_config()
    configs.append(new_config)
    state.set_pivot_configs(session_id, configs)
    
    return {'success': True, 'pivot_id': new_config['id']}

@app.put("/api/pivots/{session_id}/{pivot_id}")
async def update_pivot(session_id: str, pivot_id: str, config_update: Dict):
    df = state.get_session_data(session_id)
    if df is None:
        raise HTTPException(status_code=404, detail="No data found for session")
    
    configs = state.get_pivot_configs(session_id)
    config_index = None
    for i, config in enumerate(configs):
        if config['id'] == pivot_id:
            config_index = i
            break
    
    if config_index is None:
        raise HTTPException(status_code=404, detail="Pivot not found")
    
    # Update configuration
    configs[config_index].update(config_update)
    configs[config_index]['updated_at'] = datetime.now().isoformat()
    
    # Generate pivot table
    result = create_pivot_table(df, configs[config_index])
    if result['success']:
        configs[config_index]['pivot_df'] = result['pivot_df']
        configs[config_index]['filtered_df'] = result['filtered_df']
        configs[config_index]['error_log'] = ''
        configs[config_index]['generated_code'] = generate_python_code(configs[config_index])
    else:
        configs[config_index]['error_log'] = result.get('error', 'Unknown error')
    
    state.set_pivot_configs(session_id, configs)
    
    return {'success': result['success'], 'error': result.get('error')}

@app.delete("/api/pivots/{session_id}/{pivot_id}")
async def delete_pivot(session_id: str, pivot_id: str):
    configs = state.get_pivot_configs(session_id)
    configs = [c for c in configs if c['id'] != pivot_id]
    state.set_pivot_configs(session_id, configs)
    return {'success': True}

@app.post("/api/copy-filters/{session_id}")
async def copy_filters(session_id: str, request_data: Dict):
    """Copy filters from one pivot to another"""
    source_pivot_id = request_data.get('source_pivot_id')
    target_pivot_ids = request_data.get('target_pivot_ids', [])
    
    configs = state.get_pivot_configs(session_id)
    
    # Find source pivot
    source_config = None
    for config in configs:
        if config['id'] == source_pivot_id:
            source_config = config
            break
    
    if not source_config:
        raise HTTPException(status_code=404, detail="Source pivot not found")
    
    # Copy filters to target pivots
    updated_count = 0
    for config in configs:
        if config['id'] in target_pivot_ids:
            config['filters'] = source_config['filters'].copy()
            config['updated_at'] = datetime.now().isoformat()
            updated_count += 1
    
    state.set_pivot_configs(session_id, configs)
    
    return {'success': True, 'updated_count': updated_count}

@app.get("/api/pivot-table/{session_id}/{pivot_id}")
async def get_pivot_table(session_id: str, pivot_id: str):
    """Get pivot table data as JSON"""
    configs = state.get_pivot_configs(session_id)
    config = None
    for c in configs:
        if c['id'] == pivot_id:
            config = c
            break
    
    if not config or config.get('pivot_df') is None:
        raise HTTPException(status_code=404, detail="Pivot table not found")
    
    pivot_df = config['pivot_df']
    
    # Convert to JSON-serializable format
    if isinstance(pivot_df.columns, pd.MultiIndex):
        # Handle MultiIndex columns
        pivot_df.columns = [' | '.join(map(str, col)).strip() for col in pivot_df.columns.values]
    
    return {
        'data': pivot_df.to_dict('records'),
        'columns': pivot_df.columns.tolist(),
        'index': pivot_df.index.tolist() if hasattr(pivot_df, 'index') else []
    }

@app.post("/api/save-views/{session_id}")
async def save_views(session_id: str):
    success = state.save_views(session_id)
    return {'success': success}

@app.post("/api/load-views/{session_id}")
async def load_views(session_id: str):
    success = state.load_views(session_id)
    return {'success': success}

@app.get("/api/download/{session_id}/{pivot_id}/{file_type}")
async def download_file(session_id: str, pivot_id: str, file_type: str):
    """Download pivot table, filtered data, or generated code"""
    configs = state.get_pivot_configs(session_id)
    config = None
    for c in configs:
        if c['id'] == pivot_id:
            config = c
            break
    
    if not config:
        raise HTTPException(status_code=404, detail="Pivot not found")
    
    pivot_name = config['name'].replace(' ', '_')
    
    if file_type == 'pivot_csv':
        if config.get('pivot_df') is None:
            raise HTTPException(status_code=404, detail="No pivot table generated")
        
        csv_data = config['pivot_df'].to_csv()
        return Response(
            content=csv_data,
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=pivot_{pivot_name}.csv'}
        )
    
    elif file_type == 'filtered_csv':
        if config.get('filtered_df') is None:
            raise HTTPException(status_code=404, detail="No filtered data available")
        
        csv_data = config['filtered_df'].to_csv(index=False)
        return Response(
            content=csv_data,
            media_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename=filtered_{pivot_name}.csv'}
        )
    
    elif file_type == 'python_code':
        if not config.get('generated_code'):
            raise HTTPException(status_code=404, detail="No generated code available")
        
        return Response(
            content=config['generated_code'],
            media_type='text/x-python',
            headers={'Content-Disposition': f'attachment; filename=pivot_code_{pivot_name}.py'}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if __name__ == "__main__":
    # Create static directory if it doesn't exist
    Path("static").mkdir(exist_ok=True)
    
    print("🚀 Starting Pivot Codex V5...")
    print("📊 Advanced Multi-Pivot Table Creator")
    print("🌐 Access at: http://localhost:8000")
    print("⚡ Press Ctrl+C to stop")
    
    uvicorn.run(
        "pivot_by_codex_v5:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )