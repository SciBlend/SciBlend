from paraview.simple import *
import os
from paraview import servermanager

print("\n" + "="*50)
print("PARAVIEW MULTI-FORMAT EXPORTER")
print("="*50)

active_source = GetActiveSource()

if not active_source:
    print("\nERROR: No active source found")
    print("Please select an object in the Pipeline Browser")
    raise Exception("No object selected")

print(f"\nActive source found: {active_source.GetXMLName()}")

try:
    vtk_data = servermanager.Fetch(active_source)
    print(f"VTK data type: {vtk_data.GetClassName()}")
except Exception as e:
    print(f"Error getting VTK data: {str(e)}")
    raise Exception("Error accessing data")

def detect_data_type(data):
    if data is None:
        return "unknown"
        
    classname = data.GetClassName()
    print(f"DEBUG - VTK Class: {classname}")
    
    if "PolyData" in classname:
        if "Point" in active_source.GetXMLName():
            return "points"
        elif data.GetNumberOfPoints() > 0 and data.GetNumberOfCells() == 1:
            return "points"
        else:
            return "mesh"
    elif "UnstructuredGrid" in classname:
        return "volume"
    elif "ImageData" in classname or "StructuredGrid" in classname:
        return "volume"
    elif "MultiBlock" in classname:
        return "multiblock"
        
    return "generic"

data_type = detect_data_type(vtk_data)
print(f"Detected data type: {data_type}")

folder_path = ""
while not os.path.isdir(folder_path):
    folder_path = input("\nSave path: ").strip()
    if not os.path.isdir(folder_path):
        print("Invalid directory. Please enter a valid path.")

scene = GetAnimationScene()
scene.UpdateAnimationUsingDataTimeSteps()

timesteps = scene.TimeKeeper.TimestepValues
if not timesteps:
    timesteps = [0.0]

if data_type == "points":
    choice = input("""
Select format for point cloud (default=1):
1: CSV (.csv) - XYZ coordinates in text format
2: PLY (.ply) - Stanford Polygon Format
3: VTK (.vtk) - VTK Legacy Format
4: VTP (.vtp) - VTK XML PolyData
5: X3D (.x3d) - Web3D Standard Format

Option: """).strip() or '1'
    valid_options = {'1': 'csv', '2': 'ply', '3': 'vtk', '4': 'vtp', '5': 'x3d'}

elif data_type == "mesh":
    choice = input("""
Select format for mesh (default=1):
1: VTK (.vtk) - VTK Legacy Format
2: PLY (.ply) - Stanford Polygon Format
3: STL (.stl) - Stereolithography
4: VTP (.vtp) - VTK XML PolyData
5: X3D (.x3d) - Web3D Standard Format

Option: """).strip() or '1'
    valid_options = {'1': 'vtk', '2': 'ply', '3': 'stl', '4': 'vtp', '5': 'x3d'}

elif data_type == "volume":
    choice = input("""
Select format for volume data (default=1):
1: VTK (.vtk) - VTK Legacy Format
2: VTI (.vti) - VTK ImageData
3: VDB (.vdb) - OpenVDB
Option: """).strip() or '1'
    valid_options = {'1': 'vtk', '2': 'vti', '3': 'vdb'}

elif data_type == "multiblock":
    choice = input("""
Select format for multiblock data (default=1):
1: VTM (.vtm) - VTK XML MultiBlock (recommended)
2: CGNS (.cgns) - CFD General Notation System

Option: """).strip() or '1'
    valid_options = {'1': 'vtm', '2': 'cgns'}

else:
    choice = input("""
Select format for generic data (default=1):
1: VTK (.vtk) - VTK Legacy Format
2: VTP (.vtp) - VTK XML PolyData

Option: """).strip() or '1'
    valid_options = {'1': 'vtk', '2': 'vtp'}

if choice in valid_options:
    ext = valid_options[choice]
else:
    print("Invalid option. Using VTK format by default.")
    ext = 'vtk'

user_vdb_dims = None
if ext == 'vdb':
    dims_input = input("VDB sampling dimensions (e.g., 256 or 256,256,128, or 'n' for original) [default 128]: ").strip()
    if dims_input:
        if dims_input.lower() == 'n':
            user_vdb_dims = 'original'
            print("Using original volume extents.")
        else:
            try:
                parts = [int(x) for x in dims_input.replace(' ', '').split(',') if x != '']
                if len(parts) == 1 and parts[0] > 0:
                    user_vdb_dims = [parts[0], parts[0], parts[0]]
                elif len(parts) >= 3 and parts[0] > 0 and parts[1] > 0 and parts[2] > 0:
                    user_vdb_dims = [parts[0], parts[1], parts[2]]
                else:
                    print("Invalid input. Falling back to defaults.")
            except Exception:
                print("Invalid input. Falling back to defaults.")

total_frames = len(timesteps)
if total_frames > 1:
    print(f"\nTotal available frames: {total_frames}")
    try:
        start = int(input(f"Start frame (1-{total_frames}): ") or "1")
        end = int(input(f"End frame (1-{total_frames}): ") or str(total_frames))
        if start < 1 or end > total_frames or start > end:
            print(f"Invalid range. Using 1-{total_frames}")
            start, end = 1, total_frames
    except ValueError:
        print(f"Invalid value. Using full range 1-{total_frames}")
        start, end = 1, total_frames
else:
    start = end = 1
    print("\nStatic data (single frame)")

original_name = ""
try:
    if hasattr(active_source, 'FileName'):
        original_name = os.path.splitext(os.path.basename(active_source.FileName[0]))[0]
    elif hasattr(active_source, 'Input') and hasattr(active_source.Input, 'FileName'):
        original_name = os.path.splitext(os.path.basename(active_source.Input.FileName[0]))[0]
    else:
        original_name = active_source.GetXMLName()
except:
    original_name = "data"

print(f"\nOriginal source name: {original_name}")

naming_choice = input("""
Select naming convention (default=1):
1: Original name (e.g., {}_frame_XXXX.{})
2: Custom name
3: Generic name (data_frame_XXXX.{})

Option: """.format(original_name, ext, ext)).strip() or '1'

base_filename = ""
if naming_choice == '1':
    base_filename = original_name
    print(f"Using original name: {base_filename}")
elif naming_choice == '2':
    custom_name = input("\nEnter custom filename (without extension): ").strip()
    if custom_name:
        base_filename = custom_name
        print(f"Using custom name: {base_filename}")
    else:
        base_filename = "data"
        print("No name provided. Using 'data' as default.")
else:
    base_filename = "data"
    print("Using generic name: data")

success_count = 0
view = GetActiveViewOrCreate('RenderView')

print("\nStarting export...")

def export_to_csv(data, filepath):
    try:
        points = data.GetPoints()
        if not points:
            print("No points found in data")
            return False
            
        n_points = points.GetNumberOfPoints()
        print(f"Number of points: {n_points}")
        
        with open(filepath, 'w') as f:
            f.write("x,y,z\n")
            for i in range(n_points):
                x, y, z = points.GetPoint(i)
                f.write(f"{x},{y},{z}\n")
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {str(e)}")
        return False

def export_points(data, filepath, current_time):
    try:
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.csv':
            return export_to_csv(data, filepath)
        elif ext == '.x3d':
            try:
                view = GetActiveViewOrCreate('RenderView')
                exporter = ExportView(filepath, view=view, ExportColorLegends=1)
                return os.path.exists(filepath)
            except Exception as e:
                print(f"Error with X3D export: {str(e)}")
                return False
        elif ext == '.vdb':
            try:
                def build_vdb_volume_source(src, vtk_data):
                    """Build a volume source suitable for VDB export.
                    
                    Returns:
                        tuple: (source_proxy, resample_proxy or None)
                               resample_proxy is returned for cleanup if created
                    """
                    classname = vtk_data.GetClassName()
                    if "ImageData" in classname or "StructuredGrid" in classname:
                        if user_vdb_dims == 'original':
                            print("Using original volume dimensions.")
                            return src, None
                        elif user_vdb_dims:
                            resample = ResampleToImage(Input=src)
                            resample.UseInputBounds = 1
                            resample.SamplingDimensions = user_vdb_dims
                            return resample, resample
                        return src, None
                    print("Input is not a regular volume; resampling to ImageData for VDB export...")
                    resample = ResampleToImage(Input=src)
                    resample.UseInputBounds = 1
                    if user_vdb_dims == 'original':
                        print("Using original bounds without resampling dimensions.")
                    elif user_vdb_dims:
                        resample.SamplingDimensions = user_vdb_dims
                    else:
                        dims_env = os.environ.get('PARAVIEW_VDB_DIMS', '').strip()
                        try:
                            if dims_env:
                                parts = [int(x) for x in dims_env.replace(' ', '').split(',')]
                                if len(parts) == 1:
                                    resample.SamplingDimensions = [parts[0], parts[0], parts[0]]
                                elif len(parts) >= 3:
                                    resample.SamplingDimensions = [parts[0], parts[1], parts[2]]
                                else:
                                    resample.SamplingDimensions = [128, 128, 128]
                            else:
                                resample.SamplingDimensions = [128, 128, 128]
                        except Exception:
                            print("Invalid PARAVIEW_VDB_DIMS; using 128^3")
                            resample.SamplingDimensions = [128, 128, 128]
                    return resample, resample

                src_for_vdb, resample_to_cleanup = build_vdb_volume_source(active_source, data)
                UpdatePipeline(time=current_time, proxy=active_source)
                UpdatePipeline(time=current_time, proxy=src_for_vdb)
                SaveData(filepath, proxy=src_for_vdb)
                export_success = os.path.exists(filepath)
                
                # Clean up ResampleToImage filter to avoid memory bloat
                if resample_to_cleanup is not None:
                    try:
                        Delete(resample_to_cleanup)
                        print("Cleaned up ResampleToImage filter")
                    except Exception as cleanup_error:
                        print(f"Warning: Could not clean up ResampleToImage: {cleanup_error}")
                
                return export_success
            except Exception as e:
                print("Error exporting to VDB. Ensure the OpenVDB plugin is enabled and input is a volume or convertible to volume.")
                print(f"Details: {str(e)}")
                return False
        else:
            UpdatePipeline(time=current_time, proxy=active_source)
            SaveData(filepath, proxy=active_source)
            success = os.path.exists(filepath)
            if not success:
                print(f"Error exporting: {filepath}")
            return success
            
    except Exception as e:
        print(f"Export error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

for frame in range(start, end + 1):
    if total_frames > 1:
        current_time = timesteps[frame - 1]
        scene.TimeKeeper.Time = current_time
        scene.AnimationTime = current_time
    else:
        current_time = timesteps[0]
    print(f"Setting pipeline time to: {current_time}")
    UpdatePipeline(time=current_time, proxy=active_source)
    view.Update()
    view.ViewTime = current_time
    Render()
    
    if total_frames > 1:
        filename = f"{base_filename}_frame_{frame:04d}.{ext}"
    else:
        filename = f"{base_filename}.{ext}"
    filepath = os.path.join(folder_path, filename)
    
    print(f"\nExporting frame {frame} to {filepath}")
    
    vtk_data_frame = servermanager.Fetch(active_source)
    if export_points(vtk_data_frame, filepath, current_time):
        print(f"✓ Frame {frame} exported successfully")
        success_count += 1
    else:
        print(f"✗ Error exporting frame {frame}")
        if ext != 'vtk':
            if total_frames > 1:
                fallback_filename = f"{base_filename}_frame_{frame:04d}.vtk"
            else:
                fallback_filename = f"{base_filename}.vtk"
            fallback_path = os.path.join(folder_path, fallback_filename)
            print(f"Trying alternative format (.vtk): {fallback_path}")
            UpdatePipeline(time=current_time, proxy=active_source)
            SaveData(fallback_path, proxy=active_source)
            if os.path.exists(fallback_path):
                print(f"✓ Frame {frame} exported with alternative format")
                success_count += 1

total = end - start + 1
print(f"\nExport completed: {success_count} of {total} frames exported successfully")
if success_count < total:
    print("Some frames could not be exported. Try another format or verify the data.")
else:
    print("All frames were exported successfully!")

print("\nExport path:", folder_path)