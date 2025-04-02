# SciBlend: Advanced Data Visualization Workflows within Blender



SciBlend is a Python-based toolkit that extends Blender for data visualization. It provides specialized add-ons for multiple computational data files import, annotation, shading, and scene composition, enabling both photorealistic (Cycles) and real-time (EEVEE) rendering of large-scale and time-varying data. By combining physically based rendering with a streamlined workflow, SciBlend supports advanced visualization tasks while preserving essential scientific attributes. Comparative evaluations across multiple case studies show improvements in rendering performance, clarity, and reproducibility relative to traditional tools. This modular and user-oriented design offers a robust solution for creating publication-ready visuals of complex computational data.

This repository contains the complete SciBlend suite, the collection of Blender addons for data visualization. The suite includes:

- SciBlend Advanced Core
- SciBlend Core
- SciBlend Compositor
- SciBlend Grid Generator
- SciBlend Legend Generator
- SciBlend Notes Generator
- SciBlend Shader Generator
- SciBlend Shapes Generator

## Directory Structure
```
.
├── addons/                  # Contains all SciBlend addon packages
├── install.sh              # Main installation script
├── setup_blender_env.sh    # Dependencies setup script
├── install_addons.sh       # Addons installation script
```

## Requirements

- Linux operating system
- Python 3.11

## Quick Installation

1. Clone or download this repository
2. Open a terminal in the repository directory
3. Make the installation script executable:
```bash
chmod +x install.sh
```

4. Run the installation script:
```bash
./install.sh
```

The script will:
- Set up a Python virtual environment with all required dependencies
- Install all SciBlend addons automatically
- Create a custom Blender executable with all addons pre-configured

## Running SciBlend

After installation, you can run Blender with all SciBlend addons using:
```bash
./blender-sciblend
```

## Included Dependencies

The installation script automatically installs all required Python packages:

- VTK 9.3.0
- netCDF4
- numpy
- scipy
- matplotlib
- geopandas
- pytz
- shapely
- fiona
- Pillow

## Troubleshooting

If you encounter any issues:

1. Make sure all required files are in the correct directory structure
2. Check that Python 3.11 is installed on your system
3. Ensure you have write permissions in the installation directory

## Support

For questions, issues, or feature requests, please contact:
- Email: info@sciblend.com
