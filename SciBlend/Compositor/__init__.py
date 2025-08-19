import bpy
from . import cinematography
from . import ui

def register():
    print("Registering SciBlend Compositor") 
    try:
        cinematography.register()
        ui.register()
    except Exception as e:
        print(f"Error registering SciBlend Compositor: {str(e)}")

def unregister():
    print("Unregistering SciBlend Compositor")
    try:
        ui.unregister()
        cinematography.unregister()
    except Exception as e:
        print(f"Error unregistering SciBlend Compositor: {str(e)}")

if __name__ == "__main__":
    register()