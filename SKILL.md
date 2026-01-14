---
name: paraview
description: >
  ParaView scientific visualization for volume data and meshes. Use this skill when Claude needs to:
  (1) Visualize 3D volume data (CT, MRI, scientific simulations), (2) Create isosurfaces, slices, volume renderings,
  (3) Visualize vector fields with streamlines/glyphs, (4) Generate publication-quality screenshots,
  (5) Work with VTK, EXODUS, RAW, or other scientific data formats
---

# ParaView Scientific Visualization

> **API Documentation Version: 5.12.1**
>
> This skill's API reference is based on ParaView 5.12.1. If you're using a different version, some functions may not be available or behave differently.
>
> Check version: `from paraview.simple import GetParaViewVersion; print(GetParaViewVersion())`

## Critical: Always Use run.py Wrapper

**NEVER call scripts directly. ALWAYS use `python scripts/run.py [script]`:**

```bash
# ✅ CORRECT - Always use run.py:
python scripts/run.py launch_paraview.py
python scripts/run.py launch_paraview.py --status

# ❌ WRONG - Never call directly:
python scripts/launch_paraview.py  # May fail without venv!
```

The `run.py` wrapper automatically:
1. Creates `.venv` if needed
2. Installs all dependencies
3. Activates environment
4. Executes script properly

---

## Workflow Decision Tree

### Interactive Visualization (GUI)
Use the **Opening ParaView GUI** section to launch ParaView with pvserver

### Batch Processing (Script Generation)
1. Generate a ParaView Python script following examples
2. Execute with pvpython: `$PARAVIEW_HOME/bin/pvpython script.py`

### MCP Integration (Claude Desktop)
Use the **MCP Server** section for direct tool integration

---

## Opening ParaView GUI

When the user says "Open ParaView GUI" or requests to launch ParaView:

### Method 1: Python Script (Recommended)

```bash
# Check status first
python scripts/run.py launch_paraview.py --status

# Launch with auto-connect (starts pvserver + GUI)
python scripts/run.py launch_paraview.py

# With custom host/port
python scripts/run.py launch_paraview.py --host localhost --port 11111
```

Available options:
```bash
python scripts/run.py launch_paraview.py --help

Options:
  --host HOST        Server host (default: localhost)
  --port PORT        Server port (default: 11111)
  --no-server        Launch GUI only without starting pvserver
  --no-connect       Launch GUI without auto-connecting to server
  --server-only      Start pvserver only without launching GUI
  --single-client    Start pvserver in single-client mode
  --status           Check status of PARAVIEW_HOME and pvserver
```

### Method 2: Manual Launch

1. Start pvserver first:
   ```bash
   $PARAVIEW_HOME/bin/pvserver --server-port=11111 --multi-clients &
   ```

2. Launch ParaView GUI with auto-connect:
   ```bash
   $PARAVIEW_HOME/bin/paraview --server-url=cs://localhost:11111 &
   ```

---

## Script Reference

### Launch ParaView (`launch_paraview.py`)
```bash
python scripts/run.py launch_paraview.py                    # Full launch (server + GUI)
python scripts/run.py launch_paraview.py --status           # Check status
python scripts/run.py launch_paraview.py --server-only      # Start server only
python scripts/run.py launch_paraview.py --no-server        # GUI only
python scripts/run.py launch_paraview.py --port 22222       # Custom port
```

---

## Core Operations

### Loading Data

```python
from paraview.simple import *

# Auto-detect file type
data = OpenDataFile('path/to/file.vtk')

# VTK Legacy files
data = LegacyVTKReader(FileNames=['path/to/file.vtk'])

# EXODUS files (must UpdatePipeline before accessing bounds)
data = IOSSReader(FileName=['path/to/file.ex2'])
data.UpdatePipeline()

# RAW volume files (parse dimensions from filename like data_256x256x256_uint8.raw)
reader = OpenDataFile('path/to/file.raw')
reader.DataExtent = [0, 255, 0, 255, 0, 255]  # dims - 1
reader.DataScalarType = 'unsigned char'  # uint8/uint16/float32
reader.DataByteOrder = 'LittleEndian'
reader.FileDimensionality = 3
reader.NumberOfScalarComponents = 1
```

### Get Data Information

```python
source = GetActiveSource()

# Get bounds
bounds = source.GetDataInformation().GetBounds()
# Returns: [xmin, xmax, ymin, ymax, zmin, zmax]

# Get array range
pd = source.PointData
min_val, max_val = pd.GetArray('fieldName').GetRange()
# Or by index: pd.GetArray(0).GetRange()

# Calculate center
center = [(bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2, (bounds[4]+bounds[5])/2]
```

### Volume Rendering

```python
# Get data range
source = GetActiveSource()
pd = source.PointData
min_val, max_val = pd.GetArray(0).GetRange()

# Color transfer function
lut = GetColorTransferFunction('fieldName')
lut.RGBPoints = [min_val, 0.0, 0.0, 0.75,      # blue at min
                 (min_val + max_val)/2, 0.75, 0.75, 0.75,  # gray at mid
                 max_val, 0.75, 0.0, 0.0]      # red at max

# Opacity transfer function
# Format: [value, opacity, midpoint, sharpness, ...]
pwf = GetOpacityTransferFunction('fieldName')
pwf.Points = [min_val, 0.0, 0.5, 0.0,
              (min_val + max_val)/2, 0.5, 0.5, 0.0,
              max_val, 1.0, 0.5, 0.0]

# Display as volume
display = Show(source, renderView)
display.Representation = 'Volume'
display.ColorArrayName = ['POINTS', 'fieldName']
display.LookupTable = lut
display.ScalarOpacityFunction = pwf
```

### Isosurfaces (Contours)

```python
contour = Contour(Input=source)
contour.ContourBy = ['POINTS', 'fieldName']
contour.Isosurfaces = [0.5]  # Single or multiple isovalues: [0.3, 0.5, 0.7]
contour.PointMergeMethod = 'Uniform Binning'
Show(contour, renderView)
```

### Slices

```python
slice_filter = Slice(Input=source)
slice_filter.SliceType = 'Plane'
slice_filter.SliceType.Origin = [x, y, z]  # or use data center
slice_filter.SliceType.Normal = [0, 0, 1]  # slice normal
Show(slice_filter, renderView)
```

### Clip

```python
clip = Clip(Input=source)
clip.ClipType = 'Plane'
clip.ClipType.Origin = [0.0, 0.0, 0.0]
clip.ClipType.Normal = [1.0, 0.0, 0.0]
clip.InsideOut = False  # Flip which side to keep
Show(clip, renderView)
```

### Streamlines

```python
# Get bounds for seed placement
bounds = source.GetDataInformation().GetBounds()
center = [(bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2, (bounds[4]+bounds[5])/2]

# Create stream tracer
tracer = StreamTracer(Input=source, SeedType='Point Cloud')
tracer.Vectors = ['POINTS', 'vectorField']
tracer.IntegrationDirection = 'BOTH'  # 'FORWARD', 'BACKWARD', 'BOTH'
tracer.MaximumStreamlineLength = 50.0
tracer.SeedType.Center = center
tracer.SeedType.NumberOfPoints = 100
tracer.SeedType.Radius = 1.0

# Add tubes for visibility
tube = Tube(Input=tracer)
tube.Radius = 0.1
Show(tube, renderView)
ColorBy(tubeDisplay, ('POINTS', 'scalarField'))
```

### Glyphs

```python
glyph = Glyph(Input=source, GlyphType='Cone')  # Arrow, Cone, Sphere, Cylinder
glyph.OrientationArray = ['POINTS', 'vectorField']
glyph.ScaleArray = ['POINTS', 'vectorField']
glyph.ScaleFactor = 0.05
Show(glyph, renderView)
```

### Delaunay Triangulation (Points to Surface)

```python
delaunay = Delaunay3D(Input=points)
Show(delaunay, renderView)
```

---

## Render View Setup

```python
# Create view
renderView = CreateView('RenderView')
renderView.ViewSize = [1920, 1080]
renderView.Background = [0.1, 0.1, 0.15]  # RGB background

# Create layout
layout = CreateLayout(name='Layout')
layout.AssignView(0, renderView)

# Camera for isometric view
renderView.CameraPosition = [3.86, 3.86, 3.86]
renderView.CameraViewUp = [-0.408, 0.816, -0.408]

# Camera for +X direction view
renderView.CameraPosition = [center[0] - 1.5*max_dim, center[1], center[2]]
renderView.CameraFocalPoint = center
renderView.CameraViewUp = [0.0, 0.0, 1.0]

# Reset camera to fit all data
ResetCamera(renderView)

# Save screenshot
SaveScreenshot('output.png', renderView, ImageResolution=[1920, 1080],
               OverrideColorPalette='WhiteBackground')
```

---

## Display Properties

```python
display = GetDisplayProperties(source, renderView)

# Representation types
display.SetRepresentationType('Surface')
# Options: 'Surface', 'Surface With Edges', 'Wireframe', 'Points', 'Volume', 'Outline'

# Color by array
ColorBy(display, ('POINTS', 'fieldName'))  # or ('CELLS', 'fieldName')
display.RescaleTransferFunctionToDataRange(True)

# Solid color
ColorBy(display, None)
display.DiffuseColor = [1.0, 0.0, 0.0]  # RGB

# Opacity
display.Opacity = 0.5  # 0.0 to 1.0

# Visibility
display.Visibility = 1  # 1=visible, 0=hidden
```

---

## Color Map Presets

```python
from paraview.simple import ApplyPreset

lut = GetColorTransferFunction('fieldName')
ApplyPreset(lut, 'Cool to Warm', True)

# Available presets:
# 'Blue-Red', 'Cool to Warm', 'Viridis', 'Plasma', 'Magma', 
# 'Inferno', 'Rainbow', 'Grayscale'
```

---

## Scalar Bar (Color Legend)

```python
lut = GetColorTransferFunction('fieldName')
colorBar = GetScalarBar(lut, renderView)
colorBar.Title = 'Field Name'
colorBar.ComponentTitle = ''
colorBar.Visibility = 1
colorBar.ScalarBarLength = 0.3
```

---

## MCP Server Integration

For direct integration with Claude Desktop, use the ParaView MCP Server:

### Setup

1. Start pvserver with multi-clients:
   ```bash
   $PARAVIEW_HOME/bin/pvserver --multi-clients --server-port=11111 &
   ```

2. Connect ParaView GUI to the server (File > Connect)

3. Configure Claude Desktop's `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "ParaView": {
         "command": "/path/to/python",
         "args": ["/path/to/paraview_mcp/paraview_mcp_server.py"]
       }
     }
   }
   ```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `load_data(file_path)` | Load data file into ParaView |
| `create_isosurface(value, field)` | Create isosurface visualization |
| `create_slice(origin_x, origin_y, origin_z, normal_x, normal_y, normal_z)` | Create slice plane |
| `toggle_volume_rendering(enable)` | Enable/disable volume rendering |
| `toggle_visibility(enable)` | Show/hide active source |
| `set_active_source(name)` | Set active pipeline object |
| `get_active_source_names_by_type(source_type)` | List sources by type |
| `edit_volume_opacity(field_name, opacity_points)` | Edit opacity transfer function |
| `set_color_map(field_name, color_points)` | Set color transfer function |
| `color_by(field, component)` | Color visualization by field |
| `set_representation_type(rep_type)` | Set representation (Surface, Wireframe, etc.) |
| `get_pipeline()` | Get current pipeline structure |
| `get_available_arrays()` | List available data arrays |
| `create_streamline(seed_point_number, vector_field, ...)` | Create streamlines |
| `get_screenshot()` | Capture screenshot |
| `rotate_camera(azimuth, elevation)` | Rotate camera view |
| `reset_camera()` | Reset camera to show all data |
| `plot_over_line(point1, point2, resolution)` | Create plot over line |
| `warp_by_vector(vector_field, scale_factor)` | Warp by vector field |
| `compute_surface_area()` | Compute surface area |
| `save_contour_as_stl(stl_filename)` | Save contour as STL |

---

## Complete Example Scripts

### Volume Rendering

```python
from paraview.simple import *

# Load data
data = LegacyVTKReader(FileNames=['/path/to/volume.vtk'])

# Get range
source = GetActiveSource()
pd = source.PointData
min_val, max_val = pd.GetArray(0).GetRange()

# Transfer functions
lut = GetColorTransferFunction('var0')
lut.RGBPoints = [min_val, 0.0, 0.0, 0.75,
                 (min_val + max_val)/2, 0.75, 0.75, 0.75,
                 max_val, 0.75, 0.0, 0.0]

pwf = GetOpacityTransferFunction('var0')
pwf.Points = [min_val, 0.0, 0.5, 0.0,
              (min_val + max_val)/2, 0.5, 0.5, 0.0,
              max_val, 1.0, 0.5, 0.0]

# Create view
renderView = CreateView('RenderView')
renderView.ViewSize = [1920, 1080]
renderView.CameraPosition = [3.86, 3.86, 3.86]
renderView.CameraViewUp = [-0.408, 0.816, -0.408]

layout = CreateLayout(name='Layout')
layout.AssignView(0, renderView)

# Display as volume
display = Show(data, renderView)
display.Representation = 'Volume'
display.ColorArrayName = ['POINTS', 'var0']
display.LookupTable = lut
display.ScalarOpacityFunction = pwf

SaveScreenshot('/path/to/dvr.png', renderView, ImageResolution=[1920, 1080])
```

### Streamlines with Glyphs

```python
from paraview.simple import *

# Load data
data = IOSSReader(FileName=['/path/to/disk.ex2'])
data.UpdatePipeline()

# Get bounds
bounds = data.GetDataInformation().GetBounds()
center = [(bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2, (bounds[4]+bounds[5])/2]

# Create stream tracer
tracer = StreamTracer(Input=data, SeedType='Point Cloud')
tracer.Vectors = ['POINTS', 'V']
tracer.MaximumStreamlineLength = 20.0
tracer.SeedType.Center = center
tracer.SeedType.Radius = 2.0

# Add glyphs
glyph = Glyph(Input=tracer, GlyphType='Cone')
glyph.OrientationArray = ['POINTS', 'V']
glyph.ScaleArray = ['POINTS', 'V']
glyph.ScaleFactor = 0.06

# Add tubes
tube = Tube(Input=tracer)
tube.Radius = 0.075

# Create view
renderView = CreateView('RenderView')
renderView.ViewSize = [1920, 1080]
renderView.CameraPosition = [center[0] - 1.5*max(bounds[1]-bounds[0], bounds[3]-bounds[2]), 
                             center[1], center[2]]
renderView.CameraFocalPoint = center
renderView.CameraViewUp = [0.0, 0.0, 1.0]

layout = CreateLayout(name='Layout')
layout.AssignView(0, renderView)

# Display
tubeDisplay = Show(tube, renderView)
glyphDisplay = Show(glyph, renderView)
ColorBy(tubeDisplay, ('POINTS', 'Temp'))
ColorBy(glyphDisplay, ('POINTS', 'Temp'))
tubeDisplay.RescaleTransferFunctionToDataRange(True)
glyphDisplay.RescaleTransferFunctionToDataRange(True)

SaveScreenshot('/path/to/streamlines.png', renderView, ImageResolution=[1920, 1080])
```

### RAW Volume File

```python
from paraview.simple import *

# Parse dimensions from filename: tooth_103x94x161_uint8.raw
raw_file = '/path/to/tooth_103x94x161_uint8.raw'

reader = ImageReader(FileNames=[raw_file])
reader.DataScalarType = 'unsigned char'
reader.DataByteOrder = 'LittleEndian'
reader.DataExtent = [0, 102, 0, 93, 0, 160]  # dimensions - 1
reader.FileDimensionality = 3
reader.NumberOfScalarComponents = 1

reader.UpdatePipeline()

# Continue with visualization...
```

---

## Script Template

```python
from paraview.simple import *

# ============= Configuration =============
INPUT_FILE = '/path/to/input.vtk'
OUTPUT_FILE = '/path/to/screenshot.png'
IMAGE_SIZE = [1920, 1080]

# ============= Load Data =============
data = LegacyVTKReader(FileNames=[INPUT_FILE])
# data = IOSSReader(FileName=[INPUT_FILE])
# data.UpdatePipeline()  # Required for EXODUS

# ============= Get Data Info =============
bounds = data.GetDataInformation().GetBounds()
center = [(bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2, (bounds[4]+bounds[5])/2]

# ============= Create Filters =============
# Add your filters here

# ============= Create View =============
renderView = CreateView('RenderView')
renderView.ViewSize = IMAGE_SIZE

layout = CreateLayout(name='Layout')
layout.AssignView(0, renderView)

# ============= Display =============
display = Show(data, renderView)
# Configure display properties

# ============= Save Output =============
SaveScreenshot(OUTPUT_FILE, renderView,
               ImageResolution=IMAGE_SIZE,
               OverrideColorPalette='WhiteBackground')
```

---

## Environment Management

The virtual environment is automatically managed:
- First run creates `.venv` automatically
- Dependencies install automatically
- Everything isolated in skill directory

Manual setup (only if automatic fails):
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| PARAVIEW_HOME not set | `export PARAVIEW_HOME=/path/to/ParaView` |
| pvserver not found | Check PARAVIEW_HOME path is correct |
| Port already in use | Use `--port` to specify different port |
| Connection failed | Check firewall, try `--status` to debug |
| ModuleNotFoundError | Use `run.py` wrapper |
| "No active source" | Load data first before applying filters |
| Transfer function not working | Check field name matches array name |

---

## Resources

- `references/api-reference-5.12.1.md` - Complete Python API reference (v5.12.1)
- `references/operations.md` - Common operations quick reference
- `references/examples.md` - Complete example scripts
