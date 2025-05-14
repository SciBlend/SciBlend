# SciBlend: Advanced Data Visualization Workflows within Blender

[![DOI](https://zenodo.org/badge/959086345.svg)](https://doi.org/10.5281/zenodo.15420392)

**SciBlend** is an extensible, Python-based toolkit developed to facilitate advanced scientific visualization workflows within Blender. It integrates Blender's rendering capabilities (Cycles & EEVEE) with functionalities for processing and visualizing complex computational data, aiming to bridge the gap often found between specialized data analysis tools and general-purpose 3D creation suites.

> SciBlend enables researchers to produce detailed, interactive, and photorealistic visualizations from scientific datasets, supporting the exploration, interpretation, and communication of research findings.

---

## 🔬 Core Design Principles

SciBlend is developed based on the following principles:

-   **User-Centricity:** To provide accessible visualization tools for researchers, regardless of their prior expertise in 3D graphics, through structured interfaces and defined workflows.
-   **Modularity and Extensibility:** A collection of interoperable add-ons allows users to select tools pertinent to their specific tasks and provides a foundation for future development.
-   **Scientific Accuracy:** Emphasis is placed on the faithful representation of data attributes and scientific phenomena through precise visualization techniques.
-   **Reproducibility:** To support verifiable scientific outcomes by enabling the systematic recording and documentation of visualization parameters.
-   **Performance:** Designed to leverage Blender's rendering engines and memory management for efficient real-time animation and interaction with substantial datasets.

---

## 🌟 Key Capabilities

-   **Data Import:** Support for scientific file formats such as VTK (.vtk, .vtu, .pvtu), X3D (.x3d), NetCDF (.nc, .nc4), and Shapefiles (.shp), with a focus on preserving scientific attributes and metadata.
-   **Rendering Options:** Utilizes Blender's Cycles engine for physically-based rendering and the EEVEE engine for real-time interactive visualization.
-   **Animation Playback:** Facilitates the visualization of time-varying data, aiming for smooth playback for analysis of dynamic simulations.
-   **Data Handling:** Manages various geometric representations, including multi-resolution meshes, point clouds, and glyphs. Includes features such as Delaunay triangulation and spherical projection for specific data types.
-   **Material and Shader Control:** The Shader Generator module allows for scientifically informed material representation using established colormaps and provides tools for creating custom shaders.
-   **Scene Composition Tools:**
    -   **Legend Generator:** Creates customizable legends within Blender's compositor to aid data interpretation.
    -   **Grid Generator:** Provides customizable 2D/3D coordinate systems for spatial context.
    -   **Shapes & Notes Generators:** Offer tools for 2D compositor-based and 3D in-scene annotations.
    -   **Compositor Module:** Includes tools for scene setup, camera management, and post-processing.
-   **Scripting and Automation:** Utilizes Blender's Python API, allowing for custom script development and workflow automation.

---

##  Workflow Overview

SciBlend is designed to integrate into scientific visualization pipelines as follows:

1.  **Data Preparation (External, Optional):** Tools such as ParaView can be used for initial data processing, filtering, and preparation of large datasets. SciBlend includes ParaView macros to aid data export.
2.  **Import & Setup (SciBlend Advanced Core / Core):** Import static or time-varying datasets into Blender.
3.  **Material Application (SciBlend Shader Generator):** Apply or define shaders and colormaps based on data attributes.
4.  **Contextualization & Annotation (SciBlend Grid, Shapes, Notes Generators):** Incorporate coordinate systems and annotations.
5.  **Legend Generation (SciBlend Legend Generator):** Create legends to correlate visual elements with data values.
6.  **Scene Composition & Rendering (SciBlend Compositor):** Adjust camera settings, lighting, and render parameters using Cycles or EEVEE.

---

## 📦 Addon Suite Components

This repository contains the SciBlend suite, a collection of Blender add-ons. Each component targets specific aspects of the visualization workflow:

-   **[SciBlend Advanced Core](https://github.com/josemarinfarina/SciBlend-AdvancedCore):** For importing and processing diverse scientific data formats (VTK, NetCDF, SHP), handling various cell types, data attributes, and offering specialized geometric operations.
-   **[SciBlend Core](https://github.com/josemarinfarina/SciBlend-Core):** A module for importing ParaView X3D data, suited for straightforward visualization tasks.
-   **[SciBlend Shader Generator](https://github.com/josemarinfarina/SciBlend-ShaderGenerator):** For precise control over material properties and data representation using custom colormaps and physically-based rendering principles.
-   **[SciBlend Legend Generator](https://github.com/josemarinfarina/SciBlend-LegendGenerator):** For creating customizable legends directly within Blender's compositor.
-   **[SciBlend Grid Generator](https://github.com/josemarinfarina/SciBlend-GridGenerator):** For adding spatial context through customizable 2D and 3D coordinate systems.
-   **[SciBlend Shapes Generator](https://github.com/josemarinfarina/SciBlend-ShapesGenerator):** For non-destructive 2D annotations and visual emphasis within the compositor.
-   **[SciBlend Notes Generator](https://github.com/josemarinfarina/SciBlend-NotesGenerator):** For creating 3D in-scene annotations with clear visibility.
-   **[SciBlend Compositor](https://github.com/josemarinfarina/SciBlend-Compositor):** Provides tools for scene setup, multi-camera orchestration, and rendering management.

> **Note:** Each addon is also maintained and can be obtained from its individual repository. See links for the latest versions and specific documentation.

---

## 🗂️ Repository Structure

```
.
├── addons/                  # Bundled SciBlend addon packages (zipped)
├── install.sh               # Main installation script for the SciBlend Suite
├── setup_blender_env.sh     # Script for Blender & Python dependency setup
├── install_addons.sh        # Script for installing the bundled addons
```

---

## 🖥️ System Requirements

-   Linux operating system
-   Python 3.11
-   Blender 4.2 LTS (the installer attempts to download this version if not found)
-   ParaView 5.13.2 (recommended for data pre-processing and use of provided export macros)

---

## ⚡ Installation

1.  Clone or download this repository.
2.  Navigate to the repository directory in a terminal.
3.  Make the installer executable:
    ```bash
    chmod +x install.sh
    ```
4.  Execute the installer:
    ```bash
    ./install.sh
    ```

The script performs the following actions:
-   Attempts to download Blender 4.2 LTS if not detected locally.
-   Configures a Python environment with required dependencies.
-   Installs all SciBlend addons.
-   Creates a `./blender-sciblend` launch script.

---

## ▶️ Running SciBlend

Post-installation, launch Blender with the SciBlend suite using:
```bash
./blender-sciblend
```

---

## 🧩 Python Dependencies

The installation script manages the installation of the following Python packages:

-   VTK 9.3.0
-   netCDF4
-   numpy
-   scipy
-   matplotlib
-   geopandas
-   pytz
-   shapely
-   fiona
-   Pillow

---



## 🤝 Contributions

Contributions to the SciBlend project are welcome. This includes issue reporting, feature suggestions, or pull requests.

-   For issues concerning the overall suite or the installation process, please use the issue tracker in this main repository.
-   For contributions related to specific addons, please refer to their individual GitHub repositories (linked above).

---

## ❓ Troubleshooting

-   Verify that all files from the repository are present and in the correct structure.
-   Ensure Python 3.11 is available and correctly configured by the environment script.
-   Confirm appropriate write permissions in the installation directory.
-   For detailed issues, consult installation logs or the documentation in individual addon repositories.

---

## 💬 Support & Contact

For inquiries or support:
-   Primary Contact: info@sciblend.com
-   For issues specific to an addon, use the issue tracker on that addon's GitHub repository.

---

## 🔗 Addon Releases & Documentation

For the latest versions, features, and detailed documentation of each addon, please visit their respective repositories:

-   [SciBlend Core](https://github.com/josemarinfarina/SciBlend-Core)
-   [SciBlend Advanced Core](https://github.com/josemarinfarina/SciBlend-AdvancedCore)
-   [SciBlend Shader Generator](https://github.com/josemarinfarina/SciBlend-ShaderGenerator)
-   [SciBlend Legend Generator](https://github.com/josemarinfarina/SciBlend-LegendGenerator)
-   [SciBlend Compositor](https://github.com/josemarinfarina/SciBlend-Compositor)
-   [SciBlend Shapes Generator](https://github.com/josemarinfarina/SciBlend-ShapesGenerator)
-   [SciBlend Grid Generator](https://github.com/josemarinfarina/SciBlend-GridGenerator)
-   [SciBlend Notes Generator](https://github.com/josemarinfarina/SciBlend-NotesGenerator)

---


## 📜 Citing SciBlend

If SciBlend or its components are used in research or publications, please include the following citations:

1.  **The SciBlend Paper:**



2.  **The Software Suite:**
    > José Marín (2025). SciBlend: Advanced Data Visualization Workflows within Blender. Zenodo. DOI: 10.5281/zenodo.15420392. (Source code: https://github.com/SciBlend/SciBlend)

For specific functionalities of individual addons, please also refer to their respective repositories for appropriate citation if required.

---

> _SciBlend: Facilitating advanced scientific data visualization through integration with Blender's rendering environment._
