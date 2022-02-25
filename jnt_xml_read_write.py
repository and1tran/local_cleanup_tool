#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    Andy Tran

:synopsis:
    Write out a joint hierarchy in to an XML file. Read in a joint hierarchy form an
    XML file.

:description:
    Write out a joint hierarchy from a single root joint. User may choose where
    they want to save from a dialog box launching. User may use the read module
    to read an XML to rebuild the hierarchy in Maya.

:applications:
    Maya

"""



#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Default Python Imports
from xml.dom import minidom
import xml.etree.ElementTree as et
import os
import maya.cmds as cmds

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#

def write_xml():
    """
    Writes an XML file.

    :return: The success of the operation.
    :type: bool
    """
    # Get default Documents path. It's the default so doesn't have to be the Documents.
    doc_path = os.path.expanduser("~/")

    # Get the file path to write in.
    get_path_list = cmds.fileDialog2(fileFilter="XML (*.xml);;All Files (*.*)",
                                     dialogStyle=2, fileMode=0,
                                     startingDirectory=doc_path)

    # If nothing is returned, then return False.
    if (get_path_list == None):
        print("No file specified to write out.")
        return False
    else:
        # The file dialog will only return one file path but returns a list anyway.
        xml_path = get_path_list[0]

        # Get the selected item.
        # Input validate later for one selection and certain type.
        selected = cmds.ls(selection=True)

        # Validate the selection.
        if selected == []:
            cmds.error("No joints selected")
            return False
        elif len(selected) > 1:
            cmds.error("Too many selected")
            return False
        elif (cmds.objectType(selected[0]) != "joint"):
            cmds.error("Selected is not a joint")
            return False

        selected = selected[0]

        # Make an XML document. Send the XML doc. and selected object to write
        # its hierarchy. We will get back an XML minidom element, so append that to the
        # document.
        xml_doc = minidom.Document()
        root = deeper_write(xml_doc, selected)
        xml_doc.appendChild(root)

        # Now that we have everything in the XML instance, write the file to disk.
        xml_str = xml_doc.toprettyxml(indent="    ")
        with open(xml_path, "w") as fh:
            fh.write(xml_str)
        return True

def read_xml(xml_path=""):
    """
    Reads the contents of an XML file and returns it.

    :param xml_path: The full path to an XML file on disk.
    :type: str

    :return: The success of the operation.
    :type: bool
    """
    # Get default documents path.
    doc_path = os.path.expanduser("~/")

    # If no XML path was specified, pull up a dialog to get the path.
    if not xml_path:
        get_path_list = cmds.fileDialog2(fileFilter="XML (*.xml);;All Files (*.*)",
                                         dialogStyle=2, fileMode=1,
                                         startingDirectory=doc_path)
        print(get_path_list)
        # In the event the user clicks Cancel, then no file to read from. Otherwise
        # we're only expecting one element from the list returned from the dialog.
        if not get_path_list:
            print("No file was selected to read")
            return False
        else:
            xml_path = get_path_list[0]

    # Make sure the file exists.
    if not os.path.isfile(xml_path):
        print("The file path given can't be found on disk.")
        return None
    else:
        # Read in the XML and get the root.
        xml_fh = et.parse(xml_path)
        root = xml_fh.getroot()

        # Pass to the function to read through the hierarchy. And make a joint.
        deeper_read(root)

        return True

def deeper_write(xml_doc, obj):
    """
    The recursive function to write through the XML.

    :param xml_doc: The XML document to write on.
    :type: minidom.Document

    :param obj: The basic object to create an element on and attach to the document.
    :type: str

    :return: Success of the operation
    :type: bool
    """
    # Create an element at first. We'll attach to the document in the main function.
    parentElement = xml_doc.createElement(obj)

    # Get the world translation data and add attributes to the element.
    objTranslate = cmds.xform(obj, query=True, translation=True, worldSpace=True)
    parentElement.setAttribute("translateX", "%.3f" % objTranslate[0])
    parentElement.setAttribute("translateY", "%.3f" % objTranslate[1])
    parentElement.setAttribute("translateZ", "%.3f" % objTranslate[2])

    # If the current item doesn't have children then return the element to be parented.
    if (cmds.listRelatives(obj) == None):
        return parentElement
    # If the current item does have children we will iterate through each one.
    else:
        children = cmds.listRelatives(obj)
        for child in children:
            # ChildElement will return an element with all the children parented under
            # it so we parent to the current element, which is the parentElement.
            childElement = deeper_write(xml_doc, child)
            parentElement.appendChild(childElement)
        return parentElement

def deeper_read(obj):
    """
    The recursive function to read through the XML.

    :param obj: The parent of an element tree
    :type: xml.etree.ElementTree
    """
    # Make a list to collect the translate x, y, and z attributes. Then create the joint
    translate = [obj.attrib["translateX"],
                 obj.attrib["translateY"],
                 obj.attrib["translateZ"]]
    createdJnt = cmds.joint(name=obj.tag, absolute=True, position=translate)
    cmds.select(clear=True)

    # Loop through the children joints if any. The child joint will be created after
    # sent to deeper_read and can then be parented to the createdJnt.
    children = obj.getchildren()
    for child in children:
        deeper_read(child)
        cmds.parent(child.tag, createdJnt)
