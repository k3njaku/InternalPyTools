# Pivot Codex V5 - Advanced Multi-Pivot Table Creator

A modern, web-based application for creating and managing multiple pivot tables with an intuitive user interface optimized for both keyboard and mouse users.

## 🚀 New Features in V5

### ✨ Enhanced User Experience
- **Modern Web UI**: Complete overhaul with responsive design
- **Dual Input Support**: Optimized for both keyboard shortcuts and mouse/touchpad
- **Drag & Drop**: Upload CSV files by dragging them to the interface
- **Real-time Updates**: Instant feedback and live preview

### 📊 Advanced Pivot Management
- **Copy Filters**: Copy filter configurations between pivots with one click
- **Persistent State**: Automatically saves and restores your work across sessions
- **Multiple Pivots**: Create and manage multiple pivot tables simultaneously
- **Smart Configuration**: Intelligent form management with search and multi-select

### 💾 Better Data Handling
- **Auto-Save Views**: Never lose your configuration again
- **Export Options**: Download as CSV, Python code, or filtered data
- **Session Management**: Persistent sessions across browser reloads
- **Error Handling**: Comprehensive error reporting and recovery

### ⌨️ Keyboard Shortcuts
- `Ctrl + S`: Save all views
- `Ctrl + O`: Load saved views  
- `Ctrl + N`: Add new pivot
- `Ctrl + Enter`: Generate/update pivot table
- `Shift + Delete`: Delete active pivot

## 🛠️ Installation & Setup

### Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_v5.txt
   ```

2. **Run the Application**:
   ```bash
   python run_pivot_v5.py
   ```

3. **Access the Interface**:
   Open your browser and go to `http://localhost:8000`

### Manual Installation

If you prefer to install manually:

```bash
# Install FastAPI and dependencies
pip install fastapi uvicorn pandas python-multipart

# Start the server
cd CodexV2
python -m uvicorn pivot_by_codex_v5:app --host 0.0.0.0 --port 8000 --reload
```

## 📁 File Structure

```
PythonToolsetByK3njaku/
├── CodexV2/
│   └── pivot_by_codex_v5.py      # Main FastAPI backend
├── static/
│   ├── index.html                # Web interface
│   ├── style.css                 # Modern styling
│   └── script.js                 # Frontend logic
├── requirements_v5.txt           # Python dependencies
├── run_pivot_v5.py              # Launcher script
└── README_V5.md                 # This file
```

## 🎯 Usage Guide

### 1. Upload Data
- Drag and drop a CSV file onto the upload area, or
- Click "Select CSV File" to browse for a file
- The system automatically processes dates and data types

### 2. Create Pivots
- Click "Add New Pivot" to create a new pivot table
- Give your pivot a descriptive name
- Configure rows, columns, values, and aggregations

### 3. Apply Filters
- Add filters to refine your data
- Use various operators: equals, contains, greater than, etc.
- Copy filters between pivots using the bulk actions panel

### 4. Generate Results
- Click "Generate" to create your pivot table
- View results with interactive styling
- Download as CSV, Python code, or filtered data

### 5. Save Your Work
- Use "Save Views" to persist your configurations
- Views automatically restore when you reload the page
- Share configurations by copying the saved JSON file

## 🎨 Interface Features

### Modern Design
- **Gradient Backgrounds**: Beautiful purple-blue gradients
- **Glass Morphism**: Translucent panels with backdrop blur
- **Smooth Animations**: Fade-in effects and transitions
- **Responsive Layout**: Works on desktop, tablet, and mobile

### User-Friendly Controls
- **Multi-Select Dropdowns**: Search and select multiple columns easily
- **Smart Forms**: Auto-validation and real-time updates
- **Toast Notifications**: Clear feedback for all actions
- **Error Handling**: Helpful error messages and recovery options

### Accessibility
- **Keyboard Navigation**: Full keyboard support with focus indicators
- **High Contrast**: Automatic adaptation for high contrast mode
- **Reduced Motion**: Respects user preferences for motion
- **Screen Reader**: Semantic HTML and ARIA labels

## 🔧 Advanced Configuration

### Custom Aggregations
Available aggregation functions:
- Sum, Mean, Average, Median
- Min, Max, Count, Size
- Standard Deviation, Variance
- Number of Unique Values

### Filter Operators
Supported filter operations:
- Equals, Not Equals
- Greater/Less Than (with equals)
- Contains, Not Contains
- In List, Not In List

### Export Options
- **CSV**: Standard comma-separated values
- **Python Code**: Reusable pandas script
- **Filtered Data**: Just the filtered dataset

## 🚀 Performance

### Optimizations
- **Lazy Loading**: Components load as needed
- **Efficient Rendering**: Virtual scrolling for large tables
- **Background Processing**: Non-blocking operations
- **Smart Caching**: Reduces redundant calculations

### System Requirements
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended for large datasets)
- **Browser**: Modern browser with JavaScript enabled
- **OS**: Windows, macOS, or Linux

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**:
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Dependencies Not Installing**:
```bash
# Try upgrading pip first
python -m pip install --upgrade pip
pip install -r requirements_v5.txt
```

**Static Files Not Found**:
- Ensure the `static/` directory exists in the project root
- Check that `index.html`, `style.css`, and `script.js` are present

**Browser Not Opening**:
- Manually navigate to `http://localhost:8000`
- Check firewall settings
- Try `http://127.0.0.1:8000` instead

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify all files are in the correct locations
3. Ensure you have the required Python version
4. Try restarting the application

## 🔮 Future Enhancements

Planned features for future versions:
- **Excel Support**: Import/export Excel files
- **Database Connectivity**: Connect to SQL databases
- **Advanced Charts**: Interactive visualizations
- **Collaboration**: Share and collaborate on pivot configurations
- **API Integration**: REST API for programmatic access
- **Mobile App**: Native mobile applications

## 📝 License

This project is part of the PythonToolsetByK3njaku collection. Please refer to the main project license for usage terms.

## 🙏 Acknowledgments

Built with:
- **FastAPI**: Modern Python web framework
- **Pandas**: Powerful data manipulation library
- **Modern CSS**: Glass morphism and gradient designs
- **Vanilla JavaScript**: No framework dependencies for maximum compatibility

---

**Enjoy creating beautiful pivot tables with Pivot Codex V5! 🎉**