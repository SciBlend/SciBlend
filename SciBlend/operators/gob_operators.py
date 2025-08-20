import bpy
import socket
import json
import time
import errno
from bpy.props import StringProperty, IntProperty, BoolProperty

_active_socket = None
_is_updating = False
_buffer = b""
_expected_size = None


def show_message(message_type, message):
    """Show a popup message in Blender's UI.
    
    Args:
        message_type (str): Type of message ('ERROR' or 'INFO')
        message (str): Message text to display
    """
    def draw(self, context):
        self.layout.label(text=message)
    
    bpy.context.window_manager.popup_menu(draw, title=message, icon=message_type)


def show_error_message(message):
    """Show an error popup message.
    
    Args:
        message (str): Error message to display
    """
    show_message('ERROR', message)


def show_info_message(message):
    """Show an info popup message.
    
    Args:
        message (str): Info message to display
    """
    show_message('INFO', message)


def get_connection_error_help(error_code, host, port):
    """Get a helpful error message based on the connection error code.
    
    Args:
        error_code (int): Socket error code
        host (str): Host address that failed to connect
        port (int): Port number that failed to connect
        
    Returns:
        str: Human readable error message with troubleshooting steps
    """
    if error_code == errno.ECONNREFUSED:
        return (f"Could not connect to {host}:{port}. Make sure:\n"
                f"1. Paraview is running the GoP macro\n"
                f"2. Port {port} matches the one configured in Paraview\n"
                f"3. No firewalls are blocking the connection")
    elif error_code == errno.EHOSTUNREACH:
        return f"Cannot reach host {host}. Verify the IP address is correct."
    elif error_code == errno.ETIMEDOUT:
        return f"Connection timeout to {host}:{port}. Check network connection."
    else:
        return f"Connection error: {error_code}"


def update_mesh_safe(context, mesh_data):
    """Thread-safe wrapper for updating mesh data.
    
    Args:
        context: Blender context
        mesh_data (dict): Mesh data received from Paraview
        
    Returns:
        None
    """
    global _is_updating
    
    if _is_updating:
        return None
    
    try:
        _is_updating = True
        result = update_mesh(context, mesh_data)
        _is_updating = False
        return None
    except Exception as e:
        print(f"[GoB] Error updating mesh: {e}")
        _is_updating = False
        return None


def update_mesh(context, mesh_data):
    """Update or create a mesh from Paraview data.
    
    Args:
        context: Blender context
        mesh_data (dict): Mesh data containing vertices, faces and attributes
        
    Returns:
        bool: True if update successful, False otherwise
    """
    if not mesh_data:
        print("[GoB] Error: Empty mesh data")
        return False
        
    try:
        print(f"[GoB] Data received from Paraview:")
        for key, value in mesh_data.items():
            if key not in ['points', 'faces', 'point_data', 'cell_data']:
                print(f"  {key}: {value}")
        
        if 'points' not in mesh_data or 'faces' not in mesh_data:
            print("[GoB] No geometry data found (points or faces)")
            show_info_message("No geometry data available")
            return False
        
        source_name = mesh_data.get('source_name', 'Unknown')
        mesh_name = f"GoP_{source_name}"
        
        vertices = mesh_data['points']
        faces = mesh_data['faces']
        
        print(f"[GoB] Creating mesh with {len(vertices)} vertices and {len(faces)} faces")
        
        try:
            if mesh_name in bpy.data.meshes:
                mesh = bpy.data.meshes[mesh_name]
                mesh.clear_geometry()
            else:
                mesh = bpy.data.meshes.new(mesh_name)
                
            obj = None
            if mesh_name in bpy.data.objects:
                obj = bpy.data.objects[mesh_name]
                if obj.data != mesh:
                    obj.data = mesh
            else:
                obj = bpy.data.objects.new(mesh_name, mesh)
                context.collection.objects.link(obj)
            
            mesh.from_pydata(vertices, [], faces)
            
            if 'point_data' in mesh_data:
                for attr_name, attr_data in mesh_data['point_data'].items():
                    if attr_name in mesh.attributes:
                        mesh.attributes.remove(mesh.attributes[attr_name])
                    
                    if isinstance(attr_data['values'][0], (int, float)):
                        attr = mesh.attributes.new(
                            name=attr_name,
                            type='FLOAT',
                            domain='POINT'
                        )
                        for i, value in enumerate(attr_data['values']):
                            attr.data[i].value = float(value)
                    elif isinstance(attr_data['values'][0], (list, tuple)) and len(attr_data['values'][0]) == 3:
                        attr = mesh.attributes.new(
                            name=attr_name,
                            type='FLOAT_VECTOR',
                            domain='POINT'
                        )
                        for i, value in enumerate(attr_data['values']):
                            attr.data[i].vector = value
                    print(f"[GoB] Added point attribute: {attr_name}")
            
            if 'cell_data' in mesh_data:
                for attr_name, attr_data in mesh_data['cell_data'].items():
                    if attr_name in mesh.attributes:
                        mesh.attributes.remove(mesh.attributes[attr_name])
                    
                    if isinstance(attr_data['values'][0], (int, float)):
                        attr = mesh.attributes.new(
                            name=attr_name,
                            type='FLOAT',
                            domain='FACE'
                        )
                        for i, value in enumerate(attr_data['values']):
                            attr.data[i].value = float(value)
                    elif isinstance(attr_data['values'][0], (list, tuple)) and len(attr_data['values'][0]) == 3:
                        attr = mesh.attributes.new(
                            name=attr_name,
                            type='FLOAT_VECTOR',
                            domain='FACE'
                        )
                        for i, value in enumerate(attr_data['values']):
                            attr.data[i].vector = value
                    print(f"[GoB] Added face attribute: {attr_name}")
            
            mesh.update()
            
            for selected_obj in context.selected_objects:
                selected_obj.select_set(False)
            
            obj.select_set(True)
            context.view_layer.objects.active = obj
            
            attr_info = ""
            if 'point_data' in mesh_data:
                attr_info += f", {len(mesh_data['point_data'])} point attributes"
            if 'cell_data' in mesh_data:
                attr_info += f", {len(mesh_data['cell_data'])} face attributes"
            
            show_info_message(f"Geometry updated: {len(vertices)} vertices, {len(faces)} faces{attr_info}")
            
            return True
            
        except Exception as e:
            print(f"[GoB] Error creating/updating mesh: {e}")
            import traceback
            traceback.print_exc()
            show_error_message(f"Error creating/updating mesh: {e}")
            return False
            
    except Exception as e:
        print(f"[GoB] Error updating mesh: {e}")
        import traceback
        traceback.print_exc()
        show_error_message(f"Error updating mesh: {e}")
        return False


class GOB_OT_connect_to_paraview(bpy.types.Operator):
    """Operator to establish connection with Paraview"""
    bl_idname = "gob.connect_to_paraview"
    bl_label = "Connect to Paraview"
    
    _timer = None
    
    def execute(self, context):
        """Execute the connection to Paraview.
        
        Args:
            context: Blender context
            
        Returns:
            set: Operator return set
        """
        gob = context.scene.gob_settings
        
        if gob.is_connected:
            self.report({'INFO'}, "Already connected to Paraview")
            return {'FINISHED'}
        
        success = self.connect_client(context)
        
        if success:
            self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            return {'CANCELLED'}
    
    def modal(self, context, event):
        """Modal timer function to poll socket and process incoming data."""
        global _active_socket, _buffer, _expected_size
        gob = context.scene.gob_settings
        
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        
        if not gob.is_connected or _active_socket is None:
            self.cleanup(context)
            return {'FINISHED'}
        
        try:
            if _expected_size is None:
                chunk = _active_socket.recv(16)
                if chunk:
                    _buffer += chunk
                    if len(_buffer) >= 16:
                        header = _buffer[:16]
                        _buffer = _buffer[16:]
                        _expected_size = int(header.strip())
                        print(f"[GoB] Expecting {_expected_size} bytes of data")
            else:
                # Read payload
                remaining = _expected_size - len(_buffer)
                if remaining > 0:
                    chunk = _active_socket.recv(min(8192, remaining))
                    if chunk:
                        _buffer += chunk
                    elif remaining > 0:
                        # No data available right now
                        pass
                if _expected_size is not None and len(_buffer) >= _expected_size:
                    payload = _buffer[:_expected_size]
                    _buffer = _buffer[_expected_size:]
                    _expected_size = None
                    try:
                        json_data = json.loads(payload.decode('utf-8'))
                        bpy.app.timers.register(
                            lambda: update_mesh_safe(bpy.context, json_data.copy()),
                            first_interval=0.0
                        )
                    except json.JSONDecodeError as e:
                        print(f"[GoB] Error decoding JSON: {e}")
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"[GoB] Reception error: {e}")
            gob.is_connected = False
            self.cleanup(context)
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def cleanup(self, context):
        """Clean up timer on disconnect."""
        global _active_socket, _buffer, _expected_size
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        try:
            if _active_socket:
                _active_socket.close()
        except Exception:
            pass
        _active_socket = None
        _buffer = b""
        _expected_size = None
    
    def connect_client(self, context):
        """Establish socket connection with Paraview."""
        global _active_socket
        gob = context.scene.gob_settings
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)
            print(f"[GoB] Attempting to connect to {gob.host}:{gob.port}...")
            client_socket.connect((gob.host, gob.port))
            client_socket.setblocking(False)
            _active_socket = client_socket
            gob.is_connected = True
            print(f"[GoB] Connected to Paraview at {gob.host}:{gob.port}")
            self.report({'INFO'}, f"Connected to Paraview at {gob.host}:{gob.port}")
            return True
        except socket.error as e:
            error_code = e.errno if hasattr(e, 'errno') else 0
            error_msg = get_connection_error_help(error_code, gob.host, gob.port)
            print(f"[GoB] Connection error: {e}")
            print(f"[GoB] {error_msg}")
            self.report({'ERROR'}, f"Connection error: {e}")
            return False
        except Exception as e:
            print(f"[GoB] Unexpected error while connecting: {e}")
            self.report({'ERROR'}, f"Unexpected error while connecting: {e}")
            return False


class GOB_OT_disconnect_from_paraview(bpy.types.Operator):
    """Operator to disconnect from Paraview"""
    bl_idname = "gob.disconnect_from_paraview"
    bl_label = "Disconnect"
    
    def execute(self, context):
        """Execute the disconnection from Paraview."""
        global _active_socket
        gob = context.scene.gob_settings
        
        if not gob.is_connected:
            self.report({'WARNING'}, "Not connected to Paraview")
            return {'CANCELLED'}
        
        try:
            if _active_socket:
                try:
                    _active_socket.close()
                except:
                    pass
                _active_socket = None
            gob.is_connected = False
            self.report({'INFO'}, "Disconnected from Paraview")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error disconnecting: {e}")
            return {'CANCELLED'}


class GOB_OT_refresh_from_paraview(bpy.types.Operator):
    """Operator to request a data refresh from Paraview"""
    bl_idname = "gob.refresh_from_paraview"
    bl_label = "Refresh from Paraview"
    
    def execute(self, context):
        """Execute the refresh request to Paraview."""
        global _active_socket
        gob = context.scene.gob_settings
        
        if not gob.is_connected:
            self.report({'ERROR'}, "No connection to Paraview")
            return {'CANCELLED'}
            
        try:
            if _active_socket and isinstance(_active_socket, socket.socket):
                refresh_cmd = json.dumps({"command": "refresh"}).encode('utf-8')
                _active_socket.send(refresh_cmd)
                self.report({'INFO'}, "Requesting data from Paraview...")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Socket unavailable or invalid")
                gob.is_connected = False
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error requesting data: {e}")
            gob.is_connected = False
            _active_socket = None
            return {'CANCELLED'}


class GOBSettings(bpy.types.PropertyGroup):
    """Property group for GOB addon settings"""
    host: StringProperty(
        name="Host",
        description="Paraview server IP address",
        default="localhost"
    )
    
    port: IntProperty(
        name="Port",
        description="Port for Paraview connection",
        default=9998,
        min=1024,
        max=65535
    )
    
    is_connected: BoolProperty(
        name="Connected",
        description="Paraview connection status",
        default=False
    )


classes = (
    GOBSettings,
    GOB_OT_connect_to_paraview,
    GOB_OT_disconnect_from_paraview,
    GOB_OT_refresh_from_paraview,
)


def register():
    """Register the addon classes"""
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gob_settings = bpy.props.PointerProperty(type=GOBSettings)


def unregister():
    """Unregister the addon classes"""
    del bpy.types.Scene.gob_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()