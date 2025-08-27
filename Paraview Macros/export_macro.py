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
3: VDB (.vdb) - OpenVDB (requires plugin)

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

def export_points(data, filepath):
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
                    classname = vtk_data.GetClassName()
                    if "ImageData" in classname or "StructuredGrid" in classname:
                        return src
                    print("Input is not a regular volume; converting to voxel grid for VDB...")
                    calc = Calculator(Input=src)
                    calc.ResultArrayName = 'density'
                    calc.Function = '1'
                    resample = ResampleToImage(Input=calc)
                    resample.UseInputBounds = 1
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
                    try:
                        resample.PointDataArrays = ['density']
                    except Exception:
                        pass
                    return resample

                src_for_vdb = build_vdb_volume_source(active_source, data)
                SaveData(filepath, proxy=src_for_vdb)
                return os.path.exists(filepath)
            except Exception as e:
                print("Error exporting to VDB. Ensure the OpenVDB plugin is enabled and input is a volume or convertible to volume.")
                print(f"Details: {str(e)}")
                return False
        else:
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
        scene.TimeKeeper.Time = timesteps[frame - 1]
        scene.AnimationTime = timesteps[frame - 1]
        view.Update()
        Render()
    
    filename = f"data_frame_{frame:04d}.{ext}"
    filepath = os.path.join(folder_path, filename)
    
    print(f"\nExporting frame {frame} to {filepath}")
    
    if export_points(vtk_data, filepath):
        print(f"✓ Frame {frame} exported successfully")
        success_count += 1
    else:
        print(f"✗ Error exporting frame {frame}")
        if ext != 'vtk':
            fallback_path = os.path.join(folder_path, f"data_frame_{frame:04d}.vtk")
            print(f"Trying alternative format (.vtk): {fallback_path}")
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