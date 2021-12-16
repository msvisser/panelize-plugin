# KiCad v6 Panelization plugin
 * I am using this personally, for simple rectangular panels, not all functions are tested;
 * Should be used only for rectangular boards;
 * Edge layer should consist only of Rectangles and Lines;
 * All outline elements must have the same linewidth property;

# Version history 
## v0.9 (2021-12-16)
 * Initial commit to github;
 * Disabled some controls in the GUI (fiducials and holes are not used by my, not tested);
 * Rectangle support as an outline shape (introduced in v6);
 * Added check for unresolved text variables (introduced in v6);
 * Disregard outline linewidths in calculations (probably broken in zip file from initial source, listed below)
 

# Credits
Credits goes to these sources:
 * The work is taken from https://github.com/msvisser/panelize-plugin (it seems abandoned),
 * Working v6 sources downloaded from https://forum.kicad.info/t/plugin-panelize/31614/6?u=poco
![Modal](https://imgur.com/ppoukqk.jpg)
![Result](https://imgur.com/JzFrZMd.jpg)
