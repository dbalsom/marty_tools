# Utility scripts for IBM 5150 Bus Sniffing

Basic workflow:

 - Perform capture in DSView. Export to CSV in compressed format (this will be very large)
 - Process the exported CSV with 'export_cycles.py' to take snapshots on rising edge of CPU clock. 
 - Trim the resulting CSV with 'trim.py' based on the timeline seen in DSView to isolate the portion of the capture of interest
 - From here, you can either:
    - Decode to text format:
        - Decode the the resulting cycle-only CSV with 'decode.py' to produce a CSV with decoded fields
        - Optionally, convert the decoded CSV to Excel with highlighting and hyperlinks with 'excelify.py'
            -  Excel format has a 1M cycle limitation
        - Optionally, create a graphical visualization of CGA video output using 'csv_to_img.py'
            -  Requires a path to a PIL pixel font
            -  Requires that you captured HS and VS at minimum
    - Import to PulseView:
        - If you borrowed any address lines for other signals, process the CSV with 'fix_addr.py' to add them back.
        - Normalize the timestamps in the capture with 'normalize_clock.py'. Use a timestep of 0.00000021 for 4.77Mhz.
        - Convert the CPU clock back to square waves with 'reclock.py'. Use a timestep of 0.000000105 for 4.77Mhz.
        - Import the CSV in PulseView
            -  Provide an import string in the top field of the input dialog. The first field will be 't', followed by 'l' for each column, separated by commas.
            -  The import string for a basic capture with 32 probes will be:
                - t,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l,l
                - Add another l for each signal you stole from address lines, if any
                - Do not include a trailing comma or any whitespace (will cause error)
            - Add the i8088 and m6845 decoders from the Decoder menu
            - Reselect the READY line under the i8088 decoder, if necessary
