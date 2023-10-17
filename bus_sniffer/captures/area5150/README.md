# Area5150 Lake Effect

This is a (4.77Mhz * 2) logic dump of the Lake effect from Area5150, downsampled from a 50Mhz source capture.
It includes execution from a little ways into the loader routine, through CREDITS.COM CS:100 
and includes a few frames of the effect itself at CS:400.

The .SR file is a sigrok pulseview file and the .PVS file is the default settings. 
Additional .PVS files may be used to load markers for points of interest.

To effectively use these captures you will need to install my i8088 decoder for PulseView, found 
here:  https://github.com/dbalsom/marty_tools/tree/main/sigrok_decoders

Drop them in your PulseView/share/libsigrokdecode/decoders directory.

The A19 line was not captured due to limitations in probes (I am using 32-channel logic analyzer)

 - INTR is taken off the 8259
 - DREQ0 is taken off the 8237
 - CLK0 is taken off the 8253
 - HS, VS, and DEN are taken directly off the M6845 CRTC chip

No signals are used from the i8288, ALE can be calculated via bus status changes.

The images in this directory were created from csv_to_img.py and Photoshop. They reflect a visualization of the ISR setup portion of the effect atop a CGA video stream for synchronization.

![area5150_lake_timing_diagram_sreads_01](https://github.com/dbalsom/marty_tools/assets/7229541/bcf3b412-3428-4b97-a012-e5967b002487)
