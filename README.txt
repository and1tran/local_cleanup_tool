Joint-to-XML Reader and Writer v1.0

For Maya 2022+ and above, and Maya 2019 and 2020.
_____________________________________________________________________________________

How to run:

1. Place the xml_read_write.py file in your maya scripts folder. Maya, by default, 
will install this on your Documents folder. Your path may look like this:

C:\Users\Andy\Documents\maya\2022\scripts

2. Open Maya, and open your script editor to Python. Copy and paste the following 
code to run.

from auto_rig_v2.xml_utils.xml_read_write import write_xml, read_xml

3. When you want to write out your joint hierarchy, choose a joint and copy and run
the following line in your script editor for Python.

write_xml()

4. Afterwards, in an empty scene or without the joint hierarchy, use the following 
line in your script editor for Python to read an XML file with only joint information.

read_xml()

_____________________________________________________________________________________

CONSTRAINTS:

No other types of objects besides joints will be exported or read in.

No previous objects in the scene with the same name.

Joint orientation is not exported nor read in.