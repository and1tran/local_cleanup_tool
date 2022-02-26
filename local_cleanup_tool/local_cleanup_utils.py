#!/usr/bin/env python
#SETMODE 777

#----------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------ HEADER --#

"""
:author:
    axt170020 - Andy Tran

:synopsis:
    Cleanup your local files from your projects to free up space.

:description:
    Use Maya to open a tool that will clean up shotgrid projects' local files. This is
    assuming the pipeline supports local files for shotgrid projects.

    Any database could be attached, just this one is built for the UTD Tools using
    shotgrid.

:applications:
    Maya

"""

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- IMPORTS --#

# Default Python Imports
import os
import shutil
import time

# External
from gen_utils.pipe_enums import OS, ContextKeys, FileExtensions
from gen_utils.utils import IO
from core_tools.pipe_context import PipeContext

#----------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------- FUNCTIONS --#

#----------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------- CLASSES --#

class LocalCleanupUtil(object):
    """
    Contains the logic for LocalCleanupGUI
    """
    ASSET_DIR = "as_disc_dir"
    SHOT_DIR = "sh_disc_dir"
    def __init__(self):

        self.local_enum = OS.local # Forces the local drive

        self.local_path = None

        # context object to help find paths.
        self.context = PipeContext().basic()

        """
        The dictionary of versions with a nested dict for
        the directory path and size of the ma file within. An example:
        {"001": {"dir_path": "/Documents/work/project/type/asset/model/001",
                 "size": 6.25,
                 "last_modified": "19/01/2022"}}
        """
        self.found_versions = {}

    def get_local_versions(self, kwargs=None, context_type=None, key_str=None):
        """
        Get the local path using the class variables.

        :param kwargs: Context dictionary containing the asset/shot we want to look for
                        and all its supporting info.
        :type: dict

        :param context_type: Asset or shot.
        :type: str

        :param key_str: The asset name or disc_seq_shot we will test Maya files for.
                        So we'll append ".ma" looking for an asset, like "barrel.ma",
                        or a shot, like "ani_9000_0010.ma".
        :type: str

        :return: Success of the operation.
        :type: bool
        """
        # First get the file path with kwargs and context_type.
        if kwargs == None or context_type == None or key_str == None:
            IO.error("Not enough information passed to find local versions.")
            return None

        # Make sure that the drive is set to the local directory.
        kwargs["drive"] = self.local_enum

        if context_type == ContextKeys.ASSET:
            # Find the local path using the asset dir formula and kwargs dict just made.
            self.local_path = self.context.eval_path(formula=self.ASSET_DIR, **kwargs)

        elif context_type == ContextKeys.SHOT:
            # Find the local path using the shot dir formula and kwargs dict just made.
            self.local_path = self.context.eval_path(formula=self.SHOT_DIR, **kwargs)

        # If no path is generated, then something went wrong and we exit.
        if not self.local_path:
            IO.error("No discipline folder was able to be generated.")
            return None

        # If a path was generated, we find versions using the keys_str.
        if not self.search_for_versions(key_str):
            return False

        return True

    def search_for_versions(self, key_str=None):
        """
        Get a dictionary of the local versions if available.

        :param key_str: The asset name or disc_seq_shot we will test Maya files for.
                        So we'll append ".ma" looking for an asset, like "barrel.ma",
                        or a shot, like "ani_9000_0010.ma".
        :type: str

        :return: Success of the operation.
        :type: bool
        """
        # Check if we have a key_str to match ma files with.
        if not key_str:
            IO.error("No key_str was passed in to find local versions.")

        # Check if the folder exists and is a folder. We don't want a file.
        if not os.path.isdir(self.local_path) or not self.local_path:
            IO.error("This folder doesn't exist")
            return False

        # Check if there is anything in the folder. os.listdir will find files
        # and dirs so we'll clean up just for folders.
        disc_contents = os.listdir(self.local_path)

        # Now we loop through all the contents, and if it's a directory  with valid
        # versions then we add it to a dictionary.
        disc_folders = {}
        for item in disc_contents:

            # We don't care about the active directory.
            if item == "active":
                continue

            # Make the directory path we want to check.
            test_dir_path = os.path.join(self.local_path, item)
            if os.path.isdir(test_dir_path):
                # Make the key_str here, and if there exists a maya file
                # with the key_str then we want it.
                test_ma_file_path = test_dir_path + "/" + key_str + "." + \
                                    FileExtensions.MAYA
                if os.path.exists(test_ma_file_path):
                    # Make a dictionary with the version as the key and all its other
                    # contents as values.
                    # We store the directory path, the size of the ma file within,
                    # and the last date modified.
                    nested_dict = {"dir_path": test_dir_path}
                    ma_size = os.path.getsize(test_ma_file_path)
                    ma_size = "%5.2f" % (ma_size / 1e6)
                    nested_dict["size"] = ma_size
                    modificationTime = time.strftime("%d/%m/%Y",
                                    time.localtime(os.path.getmtime(test_ma_file_path)))
                    nested_dict["last_modified"] = modificationTime
                    disc_folders[item] = nested_dict

        # If we didn't get any folders from the discipline folder, then exit.
        if not disc_folders:
            IO.error("This does not contain any versions.")
            return False

        self.found_versions = disc_folders
        return True

    def delete_versions(self, checked=None):
        """
        This will delete the versions checked on the GUI, both in the dict and on disk.

        :param checked: Items checked on the GUI.
        :type: list

        :return: Success of the operation.
        :type: bool
        """
        # Verify there was anything checked passed in.
        if not checked:
            IO.error("No checked items passed in")
            return None

        # Now delete the files from the local directory
        for version in checked:
            dir_path = self.found_versions[version]["dir_path"]
            try:
                shutil.rmtree(dir_path)
            except WindowsError or OSError:
                IO.error("Unable to delete version: %s\n"
                        "Version was still removed from table." % version)
                continue

            # Also remove it from the found_versions dictionary.
            self.found_versions.pop(version)

        return True
