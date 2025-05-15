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

## 🗂️ Package Contents

The SciBlend project is distributed primarily as two packages, typically found on Zenodo or GitHub Releases:

1.  **SciBlend Suite Package** (e.g., `SciBlend-Suite-vX.Y.Z.zip` or `SciBlend/SciBlend-v.1.0.0.zip` as named on Zenodo)
    This is the main package containing the installation scripts and the SciBlend addons. Its structure upon extraction (from the internal `SciBlend-SciBlend-xxxxxx` folder or the repository root) is:
    ```
    .
    ├── addons/                  # Bundled SciBlend addon .zip files
    ├── install.sh               # Main installation script
    ├── setup_blender_env.sh     # Sets up Blender & Python environment
    ├── install_addons.sh        # Installs the bundled addons
    ├── README.md                # This documentation file
    ```

2.  **Pre-configured Blender for Linux** (e.g., `SciBlend_Linux_v1.0.0.zip`)
    This is a separate archive (approx. 760MB) containing Blender 4.2 for Linux with Python scientific dependencies (VTK, NumPy, etc.) pre-installed. 
    *   It is primarily intended for "Option 2: Manual Setup".
    *   This package **does not** include the SciBlend addons themselves; they must be installed from the SciBlend Suite Package.

---

## 🖥️ System Requirements

-   Linux operating system
-   Python 3.11
-   Blender 4.2 LTS (the installer attempts to download this version if not found)
-   ParaView 5.13.2 (recommended for data pre-processing and use of provided export macros)

---

## ⚡ Installation Options

You have two primary ways to set up SciBlend:

### Option 1: Using the Automated Installation Script (Recommended)

This method uses the `install.sh` script to prepare your Blender environment, install Python dependencies, and attempt to install all SciBlend addons automatically.

1.  **Download the SciBlend Suite:** Obtain the `SciBlend-Suite-vX.Y.Z.zip` (e.g., `SciBlend-Suite-v1.0.0.zip`) from the [GitHub Releases](https://github.com/SciBlend/SciBlend/releases) or the Zenodo archive. This ZIP contains the installation scripts and the `addons/` directory with all SciBlend addon .zip files.
2.  **Extract the Archive:** Unzip the downloaded file.
3.  **Navigate to the Directory:** Open a terminal in the extracted `SciBlend-Suite-vX.Y.Z` directory.
4.  **Make the Installer Executable:**
    ```bash
    chmod +x install.sh
    ```
5.  **Run the Installer:**
    ```bash
    ./install.sh
    ```
    
This script will perform the following actions:
1.  Attempt to download Blender 4.2 LTS if not detected locally.
2.  Configure a Python environment with required dependencies (VTK, netCDF4, etc.) within Blender.
3.  Install all SciBlend addons from the `addons/` directory.
4.  Create a `./blender-sciblend` launch script.

**Note on Addon Activation:** If, after running the script, some SciBlend addons do not appear in Blender's sidebar or UI panels, you may need to enable them or install them manually:
1.  Open Blender (using `./blender-sciblend`).
2.  Go to `Edit > Preferences > Add-ons`.
3.  Search for the SciBlend addons (e.g., "SciBlend Core", "SciBlend Advanced Core").
4.  If listed but unchecked, check the box to enable them.
5.  If an addon is missing entirely, click "Install...", navigate to the `addons/` directory (from the SciBlend Suite ZIP you downloaded), and select the respective addon's `.zip` file (e.g., `SciBlend_Core.zip`). Repeat for each missing addon.

### Option 2: Manual Setup with Pre-configured Blender Dependencies

This option provides a Blender 4.2 LTS environment for Linux with Python and its scientific dependencies (VTK, netCDF4, NumPy, SciPy, Matplotlib, GeoPandas, etc.) already set up. **This package does NOT include the SciBlend addons pre-installed.** You will need to install the SciBlend addons manually.

1.  **Download Pre-configured Blender (Linux):**
    *   A pre-configured Blender environment named `SciBlend_Linux_v1.0.0.zip` (or similar, check the version) is available on **Zenodo**. Look for it in the files section of the Zenodo record associated with this release ([DOI: 10.5281/zenodo.15420392](https://doi.org/10.5281/zenodo.15420392)).
2.  **Extract Blender:** Unzip `SciBlend_Linux_v1.0.0.zip` to your desired location. This folder contains a ready-to-run Blender instance.
3.  **Download the SciBlend Addons:** If you haven't already, download the `SciBlend/SciBlend-v.1.0.0.zip` from [GitHub Releases](https://github.com/SciBlend/SciBlend/releases) or Zenodo. This contains the `addons/` directory. Extract it.
4.  **Install SciBlend Addons Manually in Blender:**
    *   Run the Blender executable from the folder you extracted in step 2.
    *   Go to `Edit > Preferences > Add-ons`.
    *   Click the "Install..." button.
    *   Navigate to the `addons/` directory (from the `SciBlend-v.1.0.0/addons`)
    *   Select the `.zip` file for the first SciBlend addon you want to install (e.g., `SciBlend_AdvancedCore.zip`).
    *   Click "Install Add-on".
    *   Once installed, search for the addon and check the box next to its name to enable it.
    *   **Repeat this process (Install... and Enable) for each SciBlend addon** you wish to use from the `addons/` directory (e.g., `SciBlend_AdvancedCore.zip`, `SciBlend_ShaderGenerator.zip`, etc.).

This method is suitable for Linux users who prefer to manage Blender installations manually or have issues with the automated script, and understand they need to install each SciBlend addon individually.

---

## ▶️ Running SciBlend

Post-installation, launch Blender with the SciBlend suite using:
```bash
./blender-sciblend
```

---

## 📚 Tutorials (In Development)

Get started with SciBlend by following our video tutorials. These guides cover everything from installation to advanced features. Please note that these tutorials are currently under development.

**Accessing the SciBlend Tutorial Videos (Hosted on Vimeo):**

1.  **Tutorial 1: Installation** --- Duration: 5:27  
    [Watch Video](https://vimeo.com/1072114774/6710c26719)
2.  **Tutorial 2: Blender Basics** --- Duration: 3:38  
    [Watch Video](https://vimeo.com/1072322575/5f76df6d54)
3.  **Tutorial 3: Paraview Macros** --- Duration: 4:12  
    [Watch Video](https://vimeo.com/1072343076/bcd85df516)
4.  **Tutorial 4: Disclaimer** --- Duration: 0:50  
    [Watch Video](https://vimeo.com/1072534713/d5745037c5)
5.  **Tutorial 5: Advanced Core** --- Duration: 9:38  
    [Watch Video](https://vimeo.com/1072467895/4b891cdc36)
6.  **Tutorial 6: Shader Generator** --- Duration: 2:49  
    [Watch Video](https://vimeo.com/1072516398/ba57a7f44b)
7.  **Tutorial 7: Compositor and Rendering** --- Duration: 9:14  
    [Watch Video](https://vimeo.com/1072530634/4d23fbf807)

**Total Course Duration:** Approximately 35 minutes and 48 seconds.

**Accessing Tutorial Datasets:**

The primary "Hearts Dataset" (preprocessed for tutorial use) are not publicly hosted for direct download. Access to these materials for tutorial purposes may be requested by contacting the project maintainers:

Requests for access to other datasets mentioned in tutorials or associated research (e.g., Atrial, DualSPHysics datasets) should be directed to the support team at `info@sciblend.com`.

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
