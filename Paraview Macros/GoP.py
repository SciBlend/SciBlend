import socket
import time
import json
import traceback
from paraview.simple import *
from paraview import servermanager

def print_message(message):
    """Print a message with separator lines for visibility.
    
    Args:
        message (str): Message to print
    """
    print("\n" + "="*50)
    print(message) 
    print("="*50 + "\n")

def check_port_available(host='localhost', port=9998):
    """Check if a network port is available.
    
    Args:
        host (str): Host address to check
        port (int): Port number to check
        
    Returns:
        bool: True if port is available, False otherwise
    """
    print(f"Checking port availability {host}:{port}...")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    
    try:
        result = s.connect_ex((host, port))
        s.close()
        
        if result == 0:
            print(f"Port {port} is in use")
            return False
        else:
            print(f"Port {port} is available")
            return True
    except Exception as e:
        print(f"Error checking port: {e}")
        s.close()
        return False

def GoP():
    """Bridge between Paraview and Blender with port verification."""
    try:
        print_message("Starting GoP - Blender bridge")
        
        view = GetActiveView()
        source = GetActiveSource()
        
        if not view or not source:
            print_message("ERROR: No active view or source")
            return
        
        print(f"Active view: {view}")
        print(f"Active source: {source}")
        
        representation = GetRepresentation(source, view)
        if not representation:
            print_message("ERROR: Could not get representation")
            return
        
        print(f"Representation: {representation}")
        
        host = 'localhost'
        port = 9998
        
        if not check_port_available(host, port):
            print_message(f"ERROR: Port {port} is in use")
            print("Try using another port or restart Paraview")
            return
        
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            print(f"Attempting to bind socket to {host}:{port}...")
            server_socket.bind((host, port))
            print(f"Socket bound successfully")
            
            server_socket.listen(1)
            print_message(f"Server listening on {host}:{port}")
            print("Waiting 60 seconds for connection...")
            print("Configure Blender to connect to port 9998")
            
            server_socket.settimeout(60.0)
            
            try:
                client_socket, addr = server_socket.accept()
                print_message(f"Client connected from {addr}")
                
                while True:
                    try:
                        client_socket.settimeout(1.0)
                        command = client_socket.recv(1024).decode('utf-8')
                        
                        if not command:
                            print("Client disconnected")
                            break
                            
                        try:
                            cmd_data = json.loads(command)
                            if cmd_data.get("command") == "refresh":
                                print("Received refresh request")
                                
                                UpdatePipeline(time=0.0, proxy=source)
                                
                                extract = ExtractSurface(Input=source)
                                UpdatePipeline(time=0.0, proxy=extract)
                                polydata = servermanager.Fetch(extract)
                                
                                data = {
                                    "source_name": str(source.GetXMLName()),
                                    "view_name": str(view.GetXMLName()),
                                    "timestamp": time.time()
                                }
                                
                                try:
                                    print(f"Extracting points ({polydata.GetNumberOfPoints()} points)...")
                                    points = []
                                    for i in range(polydata.GetNumberOfPoints()):
                                        point = polydata.GetPoint(i)
                                        points.append([point[0], point[1], point[2]])
                                    data["points"] = points
                                    
                                    print(f"Extracting faces ({polydata.GetNumberOfCells()} cells)...")
                                    faces = []
                                    for i in range(polydata.GetNumberOfCells()):
                                        cell = polydata.GetCell(i)
                                        if cell.GetNumberOfPoints() >= 3:
                                            face = []
                                            for j in range(cell.GetNumberOfPoints()):
                                                face.append(cell.GetPointId(j))
                                            faces.append(face)
                                    data["faces"] = faces
                                    
                                    print(f"Data extracted: {len(points)} points, {len(faces)} faces")
                                    
                                    point_data = {}
                                    for i in range(polydata.GetPointData().GetNumberOfArrays()):
                                        array = polydata.GetPointData().GetArray(i)
                                        array_name = array.GetName()
                                        num_components = array.GetNumberOfComponents()
                                        
                                        values = []
                                        for j in range(array.GetNumberOfTuples()):
                                            if num_components == 1:
                                                values.append(array.GetValue(j))
                                            else:
                                                values.append([array.GetComponent(j, k) for k in range(num_components)])
                                        
                                        point_data[array_name] = {
                                            'num_components': num_components,
                                            'values': values
                                        }
                                    
                                    cell_data = {}
                                    for i in range(polydata.GetCellData().GetNumberOfArrays()):
                                        array = polydata.GetCellData().GetArray(i)
                                        array_name = array.GetName()
                                        num_components = array.GetNumberOfComponents()
                                        
                                        values = []
                                        for j in range(array.GetNumberOfTuples()):
                                            if num_components == 1:
                                                values.append(array.GetValue(j))
                                            else:
                                                values.append([array.GetComponent(j, k) for k in range(num_components)])
                                        
                                        cell_data[array_name] = {
                                            'num_components': num_components,
                                            'values': values
                                        }
                                    
                                    data['point_data'] = point_data
                                    data['cell_data'] = cell_data
                                    
                                    json_data = json.dumps(data)
                                    data_size = len(json_data.encode('utf-8'))
                                    
                                    size_header = f"{data_size}".encode('utf-8').ljust(16)
                                    client_socket.send(size_header)
                                    
                                    chunk_size = 8192
                                    bytes_sent = 0
                                    data_bytes = json_data.encode('utf-8')
                                    
                                    while bytes_sent < data_size:
                                        end = min(bytes_sent + chunk_size, data_size)
                                        chunk = data_bytes[bytes_sent:end]
                                        client_socket.send(chunk)
                                        bytes_sent += len(chunk)
                                        print(f"Progress: {bytes_sent}/{data_size} bytes")
                                    
                                    print("Data sent successfully")
                                    
                                except Exception as e:
                                    print(f"Error processing/sending data: {e}")
                                    traceback.print_exc()
                        except json.JSONDecodeError:
                            print("Invalid command received")
                            
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Error in communication: {e}")
                        break
                    
                client_socket.close()
            
            except Exception as e:
                print(f"Error in client connection: {e}")
                
            finally:
                server_socket.close()
            
        except Exception as e:
            print_message(f"Error creating socket: {e}")
            traceback.print_exc()
        
        print_message("GoP finished")
    except Exception as e:
        print_message(f"General error in GoP: {e}")
        traceback.print_exc()

print_message("EXECUTING GoP MACRO")
GoP()