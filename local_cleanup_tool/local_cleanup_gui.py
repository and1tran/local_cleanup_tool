#!/usr/bin/env python
# SETMODE 777

# ----------------------------------------------------------------------------------------#
# ------------------------------------------------------------------------------ HEADER --#

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

# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------- IMPORTS --#

# Default Python Imports
from PySide2 import QtGui, QtCore, QtWidgets

# External
from gen_utils.pipe_enums import Discipline, ContextKeys
from gen_utils.utils import IO
from shotgun_tools.sg_pipe_objects import ProjectFetcher
from shotgun_tools.sg_utils import get_sg_user_projects
from maya_tools.guis.maya_gui_utils import get_maya_window
from maya_tools.guis.maya_guis import ConfirmDialog
import maya_tools.utils.local_cleanup_utils as lcu


# ----------------------------------------------------------------------------------------#
# --------------------------------------------------------------------------- FUNCTIONS --#

# ----------------------------------------------------------------------------------------#
# ----------------------------------------------------------------------------- CLASSES --#

class LocalCleanupGUI(QtWidgets.QDialog):
    """
    Class for the GUI.
    """
    ASSET_DIR = "as_disc_dir"
    SHOT_DIR = "sh_disc_dir"

    def __init__(self):
        QtWidgets.QDialog.__init__(self, parent=get_maya_window())

        # Essentials for finding a project.
        self.project_reader = ProjectFetcher()
        self.project = None
        
        # GUI elements
        self.tree_view          = None
        self.project_cb         = None
        self.context_cb         = None
        self.as_seq_lbl         = None
        self.as_seq_cb          = None
        self.as_disc_shot_lbl   = None
        self.as_disc_shot_cb    = None
        self.shot_disc_lbl      = None
        self.shot_disc_cb       = None

        # Attributes for assets.
        self.asset_name = None
        self.asset_type = None
        self.asset_disc = None
        self.all_assets = None

        # Attributes for shots.
        self.all_seq   = None
        self.seq_name  = None
        self.shot_name = None
        self.shot_disc = None

        # context type to help find paths.
        self.context_type = None

        """
        The dictionary of versions with a nested dict for
        the directory path and size of the ma file within.An example:
        {"001": {"dir_path": "\Documents\work\project\/asset\model"
                             "size": 6.25}}
        """
        self.utils = lcu.LocalCleanupUtil()

        # The asset discipline list we check for.
        self.asset_disc_list = [Discipline.MODEL.short_name(),
                                Discipline.RIG.short_name(),
                                Discipline.SURFACE.short_name()]

        # The shot discipline list we check for.
        self.shot_disc_list = [Discipline.ANI.short_name(),
                               Discipline.CFX.short_name(),
                               Discipline.LIT.short_name()]

    def init_gui(self):
        """
        Builds the GUI that the user will enter info.
        """
        main_vb = QtWidgets.QVBoxLayout(self)

        # Make the header labels and combo boxes.
        main_vb.addLayout(self.header_layout())

        # Make the tree view and widget.
        main_vb.addWidget(self.tree_layout())

        # Make the total Size label
        self.total_size_lbl = QtWidgets.QLabel("Total size: %s MB" % (0))
        main_vb.addWidget(self.total_size_lbl)

        main_vb.addLayout(self.lower_layout())

        # Input for the dialog window and show.
        self.setWindowTitle("Local Cleanup Tool")
        self.setMinimumSize(500, 450)
        self.show()

    def header_layout(self):
        """
        Creates the top labels and combo boxes, like project, context, etc.

        :return: A layout asking for the project, context, asset/seq, asset disc/shot,
                 and shot disc
        :type: QtWidgets.QVBoxLayout
        """
        header_vb = QtWidgets.QVBoxLayout()

        # The project label.
        project_hb = QtWidgets.QHBoxLayout()
        project_lbl = QtWidgets.QLabel("Project:")
        project_hb.addWidget(project_lbl)

        # The project combo box.
        self.project_cb = QtWidgets.QComboBox()
        self.project_cb.addItems(["None"])
        user_projs = get_sg_user_projects()
        if user_projs:
            self.project_cb.addItems(user_projs)
        self.project_cb.currentIndexChanged['QString'].connect(self.project_changed)
        project_hb.addWidget(self.project_cb)

        # Add the project GUI contents to the layout.
        header_vb.addLayout(project_hb)

        # The context label.
        context_hb = QtWidgets.QHBoxLayout()
        context_lbl = QtWidgets.QLabel("Context:")
        context_hb.addWidget(context_lbl)

        # The context combo box.
        self.context_cb = QtWidgets.QComboBox()
        self.context_cb.addItems(["None"])
        self.context_cb.addItems([ContextKeys.ASSET, ContextKeys.SHOT])
        self.context_cb.currentIndexChanged['QString'].connect(self.context_changed)
        self.context_cb.setEnabled(False)

        # Add the context GUI contents to the layout.
        context_hb.addWidget(self.context_cb)
        header_vb.addLayout(context_hb)

        # Call the asset_shot_layout to get the other combo boxes created.
        header_vb.addLayout(self.asset_shot_layout())

        return header_vb

    def asset_shot_layout(self):
        """
        Creates the layout for the asset/shot input.

        :return: A vertical layout
        :type: QtWidgets.QVBoxLayout
        """
        as_shot_vb = QtWidgets.QVBoxLayout()

        # Make the asset/sequence label and combo box.
        as_seq_hb = QtWidgets.QHBoxLayout()
        self.as_seq_lbl = QtWidgets.QLabel("Name:")
        self.as_seq_cb = QtWidgets.QComboBox()
        self.as_seq_cb.addItems(["None"])
        self.as_seq_cb.currentIndexChanged['QString'].connect(self.as_seq_changed)
        self.as_seq_cb.setEnabled(False)

        # Add the asset/sequence label and combo box to its own hb then the as_shot_vb
        as_seq_hb.addWidget(self.as_seq_lbl)
        as_seq_hb.addWidget(self.as_seq_cb)
        as_shot_vb.addLayout(as_seq_hb)

        # Make the asset disc/shot label and combo box. They will start disabled.
        as_disc_shot_hb = QtWidgets.QHBoxLayout()
        self.as_disc_shot_lbl = QtWidgets.QLabel("Specialize:")
        self.as_disc_shot_cb = QtWidgets.QComboBox()
        self.as_disc_shot_cb.addItems(["None"])
        self.as_disc_shot_cb.currentIndexChanged['QString']. \
            connect(self.as_disc_shot_changed)
        self.as_disc_shot_cb.setEnabled(False)

        # Add the asset disc/shot label and combo box to its own hb then the as_shot_vb
        as_disc_shot_hb.addWidget(self.as_disc_shot_lbl)
        as_disc_shot_hb.addWidget(self.as_disc_shot_cb)
        as_shot_vb.addLayout(as_disc_shot_hb)

        # Make the shot discipline label. It will start hidden.
        shot_disc_hb = QtWidgets.QHBoxLayout()
        self.shot_disc_lbl = QtWidgets.QLabel("Discipline:")
        self.shot_disc_lbl.setVisible(False)

        # Make the shot discipline combo box. It will start hidden and disabled.
        self.shot_disc_cb = QtWidgets.QComboBox()
        self.shot_disc_cb.addItems(["None"] + self.shot_disc_list)
        self.shot_disc_cb.setCurrentText("None")
        self.shot_disc_cb.currentIndexChanged['QString'].connect(self.shot_disc_changed)
        self.shot_disc_cb.setEnabled(False)
        self.shot_disc_cb.setVisible(False)

        # Add the shot disc label and combo box to its own hb and then the as_shot_vb
        shot_disc_hb.addWidget(self.shot_disc_lbl)
        shot_disc_hb.addWidget(self.shot_disc_cb)
        as_shot_vb.addLayout(shot_disc_hb)

        return as_shot_vb

    def tree_layout(self):
        """
        Creates the tree view and sets its parameters.

        :return: An formatted tree view.
        :type: QtWidgets.QTreeWidget
        """
        # Creates the base tree view, hides the vertical (left) header, and
        # labels the horizontal (top)
        self.tree_view = QtWidgets.QTreeWidget()
        # self.tree_view.verticalHeader().setVisible(False)
        self.tree_view.setHeaderLabels(["", "Versions", "Size", "Last Modified"])

        # Sets the resize policy
        self.tree_view.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                      QtWidgets.QSizePolicy.Expanding)
        
        # Sets the Column Width and palette
        self.tree_view.setColumnWidth(0, 40)
        file_tree_palette = QtGui.QPalette()
        file_tree_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(200, 200, 200))
        self.tree_view.setPalette(file_tree_palette)

        return self.tree_view

    def lower_layout(self):
        """
        Creates the lower buttons.

        :return: A layout with checks buttons, the delete button, and the exit button.
        :type: QtWidgets.QVBoxLayout
        """
        delete_btn_col = "#C65E5E"
        check_btn_col  = "#4E8E9F"

        lower_vb = QtWidgets.QVBoxLayout()

        # multiple checks hb - the buttons to affect multiple checkboxes.
        multiple_checks_hb = QtWidgets.QHBoxLayout()

        # Check All button
        check_all_btn = QtWidgets.QPushButton("Check All")
        check_all_btn.clicked.connect(self.check_all_clicked)
        check_all_btn.setStyleSheet("background-color: %s" % check_btn_col)
        multiple_checks_hb.addWidget(check_all_btn)

        # Uncheck All button
        uncheck_all_btn = QtWidgets.QPushButton("Uncheck All")
        uncheck_all_btn.clicked.connect(self.uncheck_all_clicked)
        uncheck_all_btn.setStyleSheet("background-color: %s" % check_btn_col)
        multiple_checks_hb.addWidget(uncheck_all_btn)

        # Add the multiple checks hb to the main view
        lower_vb.addLayout(multiple_checks_hb)

        # Lowest hb.
        bottom_hb = QtWidgets.QHBoxLayout()

        # Make the Delete Checked btn.
        delete_btn = QtWidgets.QPushButton("Delete Checked")
        delete_btn.clicked.connect(self.delete_btn_clicked)
        delete_btn.setStyleSheet("background-color: %s" % delete_btn_col)
        bottom_hb.addWidget(delete_btn)

        # Make the exit button.
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        bottom_hb.addWidget(cancel_btn)

        lower_vb.addLayout(bottom_hb)

        return lower_vb

    def project_changed(self, item):
        """
        When the project field is changed, this function will lock the succeeding
        input boxes except the context box, and set the project.

        :param item: The selection from the combo box.
        :type: QtCore.QString
        """
        # Convert item to a string and verify the input first.
        value = str(item)
        if value == "None":
            self.project = None
            self.context_cb.setEnabled(False)
            return None

        # We want the project obj b/c we can get the assets and shots from it.
        self.project = self.project_reader.get_project_object(value)

        # Enables the context cb, disables all other combo boxes.
        self.context_cb.setEnabled(True)
        self.context_cb.setCurrentText("None")
        self.as_seq_cb.setEnabled(False)
        self.as_disc_shot_cb.setEnabled(False)

        # Disables the shot discipline options b/c we're waiting if context is a shot.
        self.set_shot_disc_state(False)

        # Make sure to clear the list view so nothing is edited mistakenly
        self.clear_tree_contents()

    def context_changed(self, item):
        """
        When the context field is changed, this function will lock the succeeding
        input boxes except the asset/sequence box, and set the context.

        :param item: The selection from the combo box.
        :type: QtCore.QString
        """
        # Convert item to a string and verify the input first.
        value = str(item)
        if value == "None":
            self.context_type = None
            self.as_seq_cb.setEnabled(False)
            return None

        # Sets the context we are looking for.
        self.context_type = item

        # Clear the asset/sequence combo box and add None to it as a default.
        self.as_seq_cb.clear()
        self.as_seq_cb.addItems(["None"])
        self.as_seq_cb.setCurrentText("None")
        self.as_seq_cb.setEnabled(True)

        # Make sure to clear the list view so nothing is edited mistakenly
        self.clear_tree_contents()

        if self.context_type == ContextKeys.ASSET:
            # If context is an asset then get the project's assets and add them to
            # as_seq_cb. We ask for the asset's discipline with as_disc_shot_lbl
            self.as_seq_lbl.setText("Asset: ")
            self.all_assets = self.project.get_asset_names()
            self.as_seq_cb.addItems(self.all_assets)

            self.as_disc_shot_lbl.setText("Discipline:")

            # We lock and hide the shot discipline b/c the asset context doesn't need it.
            self.set_shot_disc_state(False)

        elif self.context_type == ContextKeys.SHOT:
            # If context is a shot then get the project's sequences and add them to
            # as_seq_cb. We ask for the shot with as_disc_shot_lbl
            self.as_seq_lbl.setText("Sequence:")
            self.all_seq = self.project.get_sequence_names()
            self.as_seq_cb.addItems(self.all_seq)

            self.as_disc_shot_lbl.setText("Shot:")

            # We set shot_disc_cb to None waiting for the shot to be entered.
            self.shot_disc_cb.setCurrentText("None")

    def as_seq_changed(self, item):
        """
        When the asset/sequence field is changed, this function will lock the succeeding
        input boxes except the asset discipline/shot box, and set the asset/sequence.

        :param item: The selection from the combo box.
        :type: QtCore.QString
        """
        # Convert item to a string and verify the input first.
        value = str(item)
        if value == "None" or value == "":
            self.asset_name = None
            self.seq_name = None
            self.as_disc_shot_cb.setEnabled(False)
            return None

        # Clear the asset discipline/shot, the succeeding, cb and
        # set the current entry to None.
        self.as_disc_shot_cb.clear()
        self.as_disc_shot_cb.addItems(["None"])
        self.as_disc_shot_cb.setCurrentText("None")
        self.as_disc_shot_cb.setEnabled(True)

        # Make sure to clear the list view so nothing is edited mistakenly
        self.clear_tree_contents()

        if self.context_type == ContextKeys.ASSET:
            # If the context is an asset, get the type of asset from it.
            self.asset_name = value
            temp_sgAssetObj = self.project.get_asset(value)
            self.asset_type = temp_sgAssetObj.type
            # Needs to populate valid asset discipline options.
            self.as_disc_shot_cb.addItems(self.asset_disc_list)

        elif self.context_type == ContextKeys.SHOT:
            # If the context is a shot, get the a list of shots to add to the next cb.
            self.seq_name = value
            all_shots = self.project.get_shot_names(self.seq_name)
            self.as_disc_shot_cb.addItems(all_shots)

            self.shot_disc_cb.setCurrentText("None")

    def as_disc_shot_changed(self, item):
        """
        When the asset discipline/shot field is changed, this function will unlock
        the shot discipline. And the asset will look for a local path.

        :param item: The selection from the combo box.
        :type: QtCore.QString
        """
        # Convert item to a string and verify the input first.
        value = str(item)
        if value == "None" or value == "":
            self.asset_disc = None
            self.shot_name = None
            self.set_shot_disc_state(False)
            return None

        # Make sure to clear the list view so nothing is edited mistakenly
        self.clear_tree_contents()

        if self.context_type == ContextKeys.ASSET:
            self.asset_disc = value
            # We have enough info to get a local path and check for local versions.
            # We display if there are any.
            self.get_versions_and_display()


        elif self.context_type == ContextKeys.SHOT:
            # We need another combo box for shots b/c we need more info for shots.
            self.shot_name = value
            self.set_shot_disc_state(True)


    def shot_disc_changed(self, item):
        """
        When shot discipline is changed, this function will set the shot discipline and
        look for the shot local path.

        :param item: The selection from the combo box.
        :type: QtCore.QString
        """
        # Convert item to a string and verify the input first.
        value = str(item)
        if value == "None" or value == "":
            self.shot_disc = None
            return None

        # Make sure to clear the list view so nothing is edited mistakenly
        self.clear_tree_contents()

        # Look for the local path.
        self.shot_disc = value

        # We have enough info to get a local path and check for local versions.
        # We display if there are any.
        self.get_versions_and_display()

    def set_shot_disc_state(self, bool=False):
        """
        Will hide and disable the shot discipline combo box.
        """
        self.shot_disc_lbl.setVisible(bool)
        self.shot_disc_cb.setVisible(bool)
        self.shot_disc_cb.setEnabled(bool)

    def clear_tree_contents(self):
        """
        Clears the tree's contents, resets the rows, and sets the total
        size label to 0 MB.
        """
        self.tree_view.clear()
        self.total_size_lbl.setText("Total size: %s MB" % (0))

    def verify_versions(self):
        """
        Verifies if there is enough contents in the tree. We can only work with
        directories with more than 3 versions within.

        :return: Whether there is enough contents to work with in the tree.
        :type: bool
        """
        # Get the dictionary from utils.
        subject_dict = self.utils.found_versions

        # Verify there are versions at all.
        if not subject_dict:
            IO.error("No versions found.")
            return None

        # If there are no more than 3 versions in the found dict, then no need to run.
        if not len(subject_dict.keys()) > 3:
            IO.error("No versions older than the most recent 3 to work with.")
            return None

        return True

    def calculate_new_total_size(self):
        """
        Calculates the new total size of the found directory and displays.
        """
        total_size = 0
        for indv_ver_size in self.utils.found_versions.keys():
            total_size += float(self.utils.found_versions[indv_ver_size]["size"])
        total_size = "%5.2f" % (total_size)
        self.total_size_lbl.setText("Total size: %s MB" % total_size)

    def get_versions_and_display(self):
        """
        Generate a local dir path, find any versions, and populate the tree view, using
        local_cleanup_utils.
        """
        # Generate the local dir path.
        # Create a dictionary out of the GUI elements to send to utils.
        as_shot_dict = self.pack_kwargs()

        if self.context_type == ContextKeys.ASSET:
            # Send to utils to get the file path and keep it in utils.
            # If a file path was found, then get the versions inside.
            if self.utils.get_local_versions(as_shot_dict, self.context_type,
                                             self.asset_name):
                self.populate_tree_view()

        elif self.context_type == ContextKeys.SHOT:
            # Create the search string to look files like "ani_9990_0010" for shots.
            shot_str = "_".join([self.shot_disc, self.seq_name, self.shot_name])
            # Send to utils to get the file path and keep it in utils.
            # If a file path was found, then get the versions inside.
            if self.utils.get_local_versions(as_shot_dict, self.context_type,
                                             shot_str):
                self.populate_tree_view()

    def pack_kwargs(self):
        """
        Packs a kwargs dictionary to find the local file path.

        :return: Dictionary containing the asset or shot information necessary for
                 finding the path.
        :type: dict
        """
        kwargs = {"project": self.project.name}

        if self.context_type == ContextKeys.ASSET:
            # If the context is an asset, use the name, type, and discipline.
            kwargs["asset"] = self.asset_name
            kwargs["asset_type"] = self.asset_type
            kwargs["discipline"] = self.asset_disc
        elif self.context_type == ContextKeys.SHOT:
            # If the context is a shot, use the sequence, shot, and discipline.
            kwargs["sequence"] = self.seq_name
            kwargs["shot"] = self.shot_name
            kwargs["discipline"] = self.shot_disc

        return kwargs

    def populate_tree_view(self):
        """
        Populate all the versions found from the local directory.
        """
        # Verify there are versions to add.
        version_dict = self.utils.found_versions
        if not version_dict:
            IO.error("No versions found.")
            return None

        # Add the versions found into the list view in the reversed order, so most
        # recent on top.
        self.tree_view.clear()
        count = 0
        for item in reversed(list(version_dict.keys())):
            entry = QtWidgets.QTreeWidgetItem(self.tree_view,
                                              ["", item,
                                               version_dict[item]["size"] + " MB",
                                               version_dict[item]["last_modified"]])
            # Only difference between the first 3 and the rest is the disabled checkbox.
            if count < 3:
                entry.setFlags(QtCore.Qt.ItemIsUserCheckable)
            else:
                entry.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                entry.setBackground(1, QtGui.QBrush(QtGui.QColor('darkBlue')))
            entry.setData(0, QtCore.Qt.CheckStateRole, QtCore.Qt.Unchecked)

            count += 1

        # Calculate the total size and display it.
        self.calculate_new_total_size()

    def delete_btn_clicked(self):
        """
        Delete the items checked.
        """
        # Verify the contents of the tree first.
        if not self.verify_versions():
            return None

        # Get the checked items into a dictionary.
        # The key is the version checked. And value is the index in the tree widget.
        checked_dict = {}
        root = self.tree_view.invisibleRootItem()
        children_count = root.childCount()
        size_deleted = 0.0
        for item_row in range(children_count):
            item = root.child(item_row)
            if item.checkState(0):
                checked_dict[item] = item.text(1)
                size_deleted += float(item.text(2).split(" ")[1])

        # If there is nothing checked, let the user know.
        if not checked_dict:
            IO.error("There are no items checked.")
            return None

        # Make a message confirming with the user which items they selected.
        message = ("Are you sure you want to delete these versions \nfrom your local "
                   "work folder?\n\n")
        checked_dict_str = ""
        for item in checked_dict.keys():
            checked_dict_str += "%s\n" % item.text(1)
        message += checked_dict_str

        # Add how much space will be freed to the message.
        message += "\nSpace to be freed: %5.2f MB" % size_deleted

        # Confirm with the user's selection with a confirmation box.
        title = ("Final Goodbyes")
        confirm_dialog = ConfirmDialog(message=message, title=title)
        confirm_dialog.init_gui()
        if not confirm_dialog.result:
            return None

        # Clean up the tree widget first. The key is the TreeWidgetItem, and the value is
        # the version.
        for item in checked_dict:
            root.removeChild(item)

        # Now delete the files from the local directory sending in the values as a list.
        self.utils.delete_versions(checked_dict.values())

        # Calculate and display the new total size of the directory.
        self.calculate_new_total_size()

    def check_all_clicked(self):
        """
        Check all items in the tree view that are checkable.
        """
        # Verify the tree contents.
        if not self.verify_versions():
            return None

        # Loop through all rows, and if it's already checked then skip else check.
        # ItemFlags use bit masks so they are tested using bitwise operators, the "&".
        root = self.tree_view.invisibleRootItem()
        children_count = root.childCount()
        for item_row in range(children_count):
            item = root.child(item_row)
            flags = item.flags()
            if not flags & QtCore.Qt.ItemIsEnabled:
                continue
            if item.checkState(0):
                continue
            else:
                item.setCheckState(0, QtCore.Qt.Checked)

    def uncheck_all_clicked(self):
        """
        Uncheck all items in the tree view that are checkable.
        """
        # Verify the tree contents.
        if not self.verify_versions():
            return None

        # Loop through all rows, and if it's already unchecked then skip else uncheck.
        # ItemFlags use bit masks so they are tested using bitwise operators, the "&".
        root = self.tree_view.invisibleRootItem()
        children_count = root.childCount()
        for item_row in range(children_count):
            item = root.child(item_row)
            flags = item.flags()
            if not flags & QtCore.Qt.ItemIsEnabled:
                continue
            if not item.checkState(0):
                continue
            else:
                item.setCheckState(0, QtCore.Qt.Unchecked)