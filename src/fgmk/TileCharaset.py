import os
import sys
import json
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtGui, QtCore, QtWidgets
from fgmk import fifl, TileXtra, tMat

# TODO fix enter on QLineEdit

facing = ["up", "left", "down", "right"]
standardStateset = ["normalSet"]
standardMovement = ["standing", "walking"]

GAMEFOLDER = "gamefolder"

class BaseFormat:

    def __init__(self):
        self.jsonTree = {}
        self.filename = ""

    def new(self):
        self.jsonTree = {}

    def save(self, charsn=None):
        if(charsn == None):
            chartosave = self.filename
        else:
            chartosave = charsn
        f = open(chartosave, "w")
        tMat.fwriteKeyVals(self.jsonTree, f)
        f.close()

    def exportJS(self, charsn):
        f = open(charsn, "w")
        f.write("var " + self.levelName + "= {\n")
        tMat.fwriteKeyValsJS(self.jsonTree, f)
        f.write("};")
        f.close()

    def load(self, charsn):
        f = open(charsn, "r")
        self.jsonTree = json.load(f)
        f.close()
        self.filename = charsn


class CharasetFormat(BaseFormat):

    def __init__(self):
        super().__init__()

        self.size = [32, 64]
        self.boxsize = 32

        self.new()

    def new(self):
        self.jsonTree = {"Charaset": {}}

    def setTileImage(self, tileImage):
        self.jsonTree["Charaset"]["tileImage"] = tileImage

    def getTileImage(self):
        if "tileImage" in self.jsonTree["Charaset"]:
            return self.jsonTree["Charaset"]["tileImage"]
        else:
            return False

    def addCharaset(self, name, jsonTree={}):
        self.jsonTree["Charaset"][name] = jsonTree

    def getCharasets(self):
        charasetsa = self.jsonTree["Charaset"]
        excludes = ["tileImage"]
        resultset = [key for key, value in charasetsa.items()
                     if key not in excludes]
        return sorted(resultset)

    def getAnimation(self, charaset):
        csetTree = self.jsonTree["Charaset"][charaset]
        csetTL1 = sorted(csetTree)
        tests = standardMovement[:]
        tests.append(sorted(csetTree)[0])
        for test in tests:
            if test in csetTL1:
                if (isinstance(csetTree[test], list)):
                    return csetTree[test]
                else:
                    csetTL2 = sorted(csetTree[test])
                    for face in sorted(facing):
                        if face in csetTL2:
                            return csetTree[test][face]


class BaseCharaset:

    def __init__(self, image_file):

        self.imgFile = image_file
        self.hasimage = self.init(image_file)

    def init(self, image_file):
        if(image_file == None):
            return False

        if(os.path.isfile(image_file)):
            self.bcset = []
            self.boxw = 32
            self.boxh = 64
            self.boxsize = (self.boxw, self.boxh)
            self.imageFile = Image.open(image_file)
            if self.imageFile.size[0] % self.boxsize[0] == 0 and self.imageFile.size[1] % self.boxsize[1] == 0:
                currentx = 0
                currenty = 0
                tilei = 0
                yj = 0
                while currenty < self.imageFile.size[1]:
                    self.bcset.append([])
                    while currentx < self.imageFile.size[0]:
                        imageTemp = self.imageFile.crop(
                            (currentx, currenty, currentx + self.boxw, currenty + self.boxh))
                        self.bcset[yj].append([imageTemp, imageTemp.resize((self.boxw * 2, self.boxh * 2), Image.NEAREST),
                                               imageTemp.resize((int(self.boxw * 0.5), int(self.boxh * 0.5)), Image.NEAREST)])
                        currentx += self.boxw

                    yj += 1
                    currenty += self.boxh
                    currentx = 0

                return True

            else:
                print("error:Your file width and height are not good to {0}x{1} pixel charaset!".format(
                    self.boxw, self.boxh))

        return False

    def getTileSetImage(self, TileType):
        # print(TileType)
        tileImage = ImageQt(self.tileset[TileType[1]][TileType[0]])
        pixmap = QtGui.QPixmap.fromImage(tileImage)
        image = QtGui.QPixmap(pixmap)
        return image


class CharaPalette(QWidget):

    clicked = pyqtSignal()

    def __init__(self, base_image=None, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.Grid = QGridLayout(self)

        self.Grid.setHorizontalSpacing(0)
        self.Grid.setVerticalSpacing(0)
        self.Grid.setSpacing(0)
        self.Grid.setContentsMargins(0, 0, 0, 0)
        self.boxw = 32
        self.boxh = 64
        self.boxsize = (self.boxw, self.boxh)

        self.scale = 2

        self.charasetList = []

        if(base_image != None):
            self.update(base_image)

    def update(self, base_image):
        self.baseImage = base_image
        self.draw()

    def draw(self):

        self.myBC = BaseCharaset(self.baseImage)

        self.setVisible(False)

        self.charHei = len(self.myBC.bcset)
        self.charWid = len(self.myBC.bcset[0])

        if len(self.charasetList) > 1:
            for collum in self.charasetList:
                for wdgt in collum:
                    wdgt.deleteLater()
                    wdgt = None
            self.charasetList = []

        # get the background numbers and use to get the tiles
        # for i in height
        for iy in range(self.charHei):
            # for j in width
            self.charasetList.append([])
            for jx in range(self.charWid):
                self.charasetList[iy].append(CharaTile(self))
                self.Grid.addWidget(self.charasetList[iy][jx], iy, jx)
                self.charasetList[iy][jx].init(
                    self.myBC.bcset, self.boxsize, [jx, iy], self.scale)
                self.charasetList[iy][jx].clicked.connect(self.csetSinClick)

        self.resize(self.charWid * self.boxw * self.scale,
                    self.charHei * self.boxh * self.scale)

        self.setVisible(True)

    def csetSinClick(self):
        self.rValue = (self.sender().charType, self.myBC.bcset, self.scale)
        self.clicked.emit()


class CharaTile(QLabel):

    def __init(self, parent):
        super().__init__(parent)

        self.charType = []
        self.boxw = 32
        self.boxh = 64
        self.boxsize = (self.boxw, self.boxh)
        self.setMinimumSize(QSize(self.boxw, self.boxh))

    clicked = pyqtSignal()
    rightClicked = pyqtSignal()

    def init(self, bcset, boxsize, charType, scale=1):
        self.charType = charType
        self.boxsize = boxsize
        self.boxw = self.boxsize[0]
        self.boxh = self.boxsize[1]

        if(scale == 2):
            tempscale = 1
        elif(scale == 0.5):
            tempscale = 2
        else:
            tempscale = 0

        Composite = bcset[charType[1]][charType[0]][tempscale]
        pixmap = QtGui.QPixmap.fromImage(ImageQt(Composite))
        self.setPixmap(pixmap)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.RightButton:
            self.rightClicked.emit()
        else:
            self.clicked.emit()


class csetsItem(QtWidgets.QListWidgetItem):

    def __init__(self, aname, jsonTree={}):
        super().__init__(aname)

        self.aname = aname
        self.jsonTree = jsonTree


class AnimNamesItem(QtWidgets.QListWidgetItem):

    def __init__(self, aname, isgroup=False, isparent=False):
        super().__init__(aname)

        self.isgroup = isgroup
        self.isparent = isparent
        self.ischildof = False
        self.aname = aname
        aarray = []
        self.setData(Qt.UserRole, aarray)

    def setIschildof(self, parent):
        self.ischildof = parent

    def getIschildof(self):
        return self.ischildof

    def setAarray(self, aarray):
        self.setData(Qt.UserRole, aarray)

    def getAarray(self):
        return self.data(Qt.UserRole)


class CsetAItem(QtWidgets.QListWidgetItem):

    def __init__(self, charType, bcset, scale=1):
        super().__init__()

        if(scale == 2):
            tempscale = 1
        elif(scale == 0.5):
            tempscale = 2
        else:
            tempscale = 0

        Composite = bcset[charType[1]][charType[0]][tempscale]
        pixmap = QtGui.QPixmap.fromImage(ImageQt(Composite))

        f = QFont()
        f.setPointSize(1)
        self.setFont(f)

        self.setIcon(QIcon(pixmap))
        self.setData(Qt.UserRole, charType)

    def getCharType(self):
        return self.data(Qt.UserRole)


class AnimatedCharaTile(QLabel):

    def __init__(self, parent=None, scale=2):
        super().__init__(parent)

        self.charType = []
        self.boxw = 32
        self.boxh = 64
        self.scale = scale
        self.boxsize = (self.boxw, self.boxh)
        self.whsize = QSize(self.boxw * scale, self.boxh * scale)
        self.setFixedSize(self.whsize)
        self._timer = QtCore.QTimer(interval=100,
                                    timeout=self._animation_step)

        self.clearAnim()

    def setACTImage(self, charType):
        self.charType = charType
        scale = self.scale

        if(scale == 2):
            tempscale = 1
        elif(scale == 0.5):
            tempscale = 2
        else:
            tempscale = 0

        Composite = self.bcset[charType[1]][charType[0]][tempscale]
        pixmap = QtGui.QPixmap.fromImage(ImageQt(Composite))
        self.setPixmap(pixmap)

    def clearAnim(self):
        self._timer.stop()
        pixmap = QPixmap(self.boxw * self.scale, self.boxh * self.scale)
        pixmap.fill(Qt.white)
        self.setPixmap(pixmap)

    def setAnimArray(self, bcset, aarray):
        self.aarray = aarray
        self.bcset = bcset
        self._current_frame = 0
        self.play()

    def play(self):
        self._timer.start()

    def _animation_step(self):
        if(len(self.aarray) > 0):
            self.setACTImage(self.aarray[self._current_frame])
            self._current_frame += 1
            if self._current_frame >= len(self.aarray):
                self._current_frame = 0


def isFacing(test):
    for i in range(len(facing)):
        if(test == facing[i]):
            return True
    return False


def isParent(jsonTreeItem):
    for anim in jsonTreeItem:
        if(isFacing(anim)):
            return True

    return False


class CharasetSelector(QWidget):

    def __init__(self, parent=None, ssettings={}, cset=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.VBox = QVBoxLayout(self)
        self.ssettings = ssettings

        if(self.ssettings == {}):
            self.ssettings["gamefolder"] = os.path.abspath(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../Game/"))

        if (cset is not None):
            self.cset = cset
        else:
            self.cset = CharasetFormat()

        self.csetList = QListWidget()
        self.myBC = BaseCharaset(None)
        self.update()

        self.previewer = AnimatedCharaTile()

        self.VBox.addWidget(self.previewer)
        self.VBox.addWidget(self.csetList)

        self.csetList.itemSelectionChanged.connect(self.changed)
        self.csetList.setCurrentRow(0)

    def update(self):
        if "gamefolder" in self.ssettings:
            for f in os.listdir(os.path.join(self.ssettings["gamefolder"], fifl.CHARASETS)):
                if f.endswith(".json"):
                    break

            f = os.path.join(self.ssettings["gamefolder"], fifl.CHARASETS, f)
            if(os.path.isfile(f)):
                self.cset.load(f)

                self.csetList.clear()

                for charaset in self.cset.getCharasets():
                    self.csetList.addItem(charaset)

        if(self.cset.getTileImage()):
            fimg = os.path.join(
                self.ssettings["gamefolder"], fifl.IMG, self.cset.getTileImage())
            self.myBC.init(fimg)

    def reset(self):
        if(self.csetList.count() > 0):
            self.csetList.setCurrentRow(0)

    def changed(self):
        if(len(self.csetList.selectedItems()) > 0 and self.myBC.hasimage):
            row = self.csetList.row(self.csetList.selectedItems()[0])
            charaset = self.cset.getCharasets()[row]
            aarray = self.cset.getAnimation(charaset)

            self.previewer.setAnimArray(self.myBC.bcset, aarray)

    def select(self, item):
        for itemIndex in range(self.csetList.count()):
            if (self.cset.getCharasets()[itemIndex] == item):
                self.csetList.setCurrentRow(itemIndex)

    def getValue(self):
        row = self.csetList.row(self.csetList.selectedItems()[0])
        charaset = str(self.cset.getCharasets()[row])
        return charaset


class CharasetPreviewer(QWidget):

    def __init__(self, parent=None, ssettings={}, cset=None, scale=2, **kwargs):
        super().__init__(parent, **kwargs)

        self.ssettings = ssettings

        if(self.ssettings == {}):
            self.ssettings["gamefolder"] = os.path.abspath(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../Game/"))

        if (cset is not None):
            self.cset = cset
        else:
            self.cset = CharasetFormat()

        self.cset.getTileImage()
        self.myBC = BaseCharaset(None)
        self.update()

        self.previewer = AnimatedCharaTile(self, scale)
        self.whsize = self.previewer.whsize
        self.setFixedSize(self.whsize)

    def update(self):
        if "gamefolder" in self.ssettings and (self.ssettings["gamefolder"] != ""):
            for f in os.listdir(os.path.join(self.ssettings["gamefolder"], fifl.CHARASETS)):
                if f.endswith(".json"):
                    break

            f = os.path.join(self.ssettings["gamefolder"], fifl.CHARASETS, f)
            if(os.path.isfile(f)):
                self.cset.load(f)

        if(self.cset.getTileImage()):
            fimg = os.path.join(
                self.ssettings["gamefolder"], fifl.IMG, self.cset.getTileImage())
            self.myBC.init(fimg)

    def stop(self):
        self.previewer.clearAnim()

    def select(self, item):
        charasets = self.cset.getCharasets()
        for charaset in charasets:
            if (charaset == item):
                aarray = self.cset.getAnimation(charaset)
                self.previewer.setAnimArray(self.myBC.bcset, aarray)
                return True

        return False


class CharasetEditorWidget(QDialog):

    def __init__(self, parent=None, ssettings={}, **kwargs):
        super().__init__(parent, **kwargs)

        self.cset = CharasetFormat()

        self.ssettings = ssettings

        self.tileImage = ""

        self.updating = False

        self.HBox = QHBoxLayout(self)
        self.HBox.setAlignment(Qt.AlignTop)

        self.csetsOpenEdit = QLineEdit()
        self.csetsNewButton = QPushButton("New")
        self.csetsOpenButton = QPushButton("Open")
        self.csetsSaveButton = QPushButton("Save")

        self.csetsNewButton.clicked.connect(self.charasetNew)
        self.csetsOpenButton.clicked.connect(self.charasetOpen)
        self.csetsSaveButton.clicked.connect(self.charasetSave)

        HBoxOpen = QHBoxLayout()
        HBoxOpen.addWidget(self.csetsNewButton)
        HBoxOpen.addWidget(self.csetsOpenButton)
        HBoxOpen.addWidget(self.csetsSaveButton)

        self.csetsEntry = QLineEdit()
        self.csetsAddButton = QPushButton("Add")
        self.csetsDelButton = QPushButton("Delete")
        self.csetsAddButton.clicked.connect(self.csetsAddAction)
        self.csetsEntry.returnPressed.connect(self.csetsAddAction)
        self.csetsDelButton.clicked.connect(self.csetsDelAction)
        HBoxEntry = QHBoxLayout()
        HBoxEntry.addWidget(self.csetsEntry)
        HBoxEntry.addWidget(self.csetsAddButton)
        HBoxEntry.addWidget(self.csetsDelButton)

        self.csetsList = QListWidget()
        self.csetsList.itemSelectionChanged.connect(
            self.csetsListSelectionChanged)

        VBoxCSets = QVBoxLayout()
        VBoxCSets.addWidget(QLabel("Charaset File:"))
        VBoxCSets.addWidget(self.csetsOpenEdit)
        VBoxCSets.addLayout(HBoxOpen)
        VBoxCSets.addWidget(QLabel("Entry name to add:"))
        VBoxCSets.addLayout(HBoxEntry)
        VBoxCSets.addWidget(self.csetsList)

        self.palette = CharaPalette()
        self.palette.clicked.connect(self.animselected)
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidget(self.palette)
        self.scrollArea.setMinimumWidth(
            self.palette.boxw * self.palette.scale * 3 + 16)
        self.scrollArea.setMinimumHeight(
            self.palette.boxh * self.palette.scale * 4 + 16)

        self.palImageFile = QLineEdit()
        self.palImageFileButton = QPushButton("Open")
        self.palImageFileButton.clicked.connect(self.imgOpen)

        self.animList = QListWidget()
        self.animList.setIconSize(QSize(64, 128))
        self.animList.setFlow(QListWidget.LeftToRight)
        self.animList.setMinimumWidth(
            self.palette.boxw * self.palette.scale * 4 + 48)
        self.animList.setMinimumHeight(
            self.palette.boxh * self.palette.scale * 2 + 16)
        self.animList.setMaximumHeight(
            self.palette.boxh * self.palette.scale * 2 + 16)
        self.animList.setDragDropMode(QAbstractItemView.InternalMove)
        self.animListDel = QPushButton("Delete Frame")
        self.animListDel.clicked.connect(self.animListDelAction)

        animListModel = self.animList.model()
        animListModel.layoutChanged.connect(self.animListUpdated)
        animListModel.rowsInserted.connect(self.animListUpdated)

        self.animNamesEntry = QLineEdit()
        self.animNamesEntry.returnPressed.connect(self.animNamesAddAction)
        self.animNamesAdd = QPushButton("Add animation")
        self.animNamesAdd.clicked.connect(self.animNamesAddAction)
        self.animNamesCheckBNF = QCheckBox("No facing")
        self.animNamesDel = QPushButton("Delete")
        self.animNamesDel.clicked.connect(self.animNamesDelAction)
        self.animNames = QListWidget()
        self.animNames.itemSelectionChanged.connect(
            self.animNamesSelectionChanged)
        self.animNames.itemChanged.connect(self.animNamesChanged)

        self.animPreview = AnimatedCharaTile()

        HBoxCharaPalName = QHBoxLayout()
        HBoxCharaPalName.addWidget(self.palImageFile)
        HBoxCharaPalName.addWidget(self.palImageFileButton)

        VBoxCharaPalette = QVBoxLayout()
        VBoxCharaPalette.addWidget(QLabel("Image file to load:"))
        VBoxCharaPalette.addLayout(HBoxCharaPalName)
        VBoxCharaPalette.addWidget(QLabel("Available frames:"))
        VBoxCharaPalette.addWidget(self.scrollArea)

        HBoxANE = QHBoxLayout()
        HBoxANE.addWidget(self.animNamesEntry)
        HBoxANE.addWidget(self.animNamesAdd)
        HBoxANE.addWidget(self.animNamesCheckBNF)
        HBoxANE.addWidget(self.animNamesDel)

        HBoxAnim = QHBoxLayout()
        HBoxAnim.addWidget(self.animPreview)
        HBoxAnim.addWidget(self.animListDel)

        VBoxCharaAnim = QVBoxLayout()

        VBoxCharaAnim.addWidget(QLabel("Animation Sequence:"))
        VBoxCharaAnim.addLayout(HBoxANE)
        VBoxCharaAnim.addWidget(self.animNames)
        VBoxCharaAnim.addLayout(HBoxAnim)
        VBoxCharaAnim.addWidget(QLabel("Animation Frames:"))
        VBoxCharaAnim.addWidget(self.animList)

        self.HBox.addLayout(VBoxCSets)
        self.HBox.addLayout(VBoxCharaPalette)
        self.HBox.addLayout(VBoxCharaAnim)

        self.animNamesEntry.textChanged.connect(self.animNamesEnable)
        self.animNamesAdd.setEnabled(False)
        self.animNames.setEnabled(False)

        if "gamefolder" in self.ssettings:
            for f in os.listdir(os.path.join(self.ssettings["gamefolder"], fifl.CHARASETS)):
                if f.endswith(".json"):
                    break

            f = os.path.join(self.ssettings["gamefolder"], fifl.CHARASETS, f)
            if(os.path.isfile(f)):
                self.__charasetOpen(f)

    def csetsAddAction(self):
        charsetName = str(self.csetsEntry.text()).strip()
        jsonTree = {}
        self.csetsList.addItem(csetsItem(charsetName, jsonTree))

    def csetsDelAction(self):
        if (len(self.csetsList.selectedItems()) > 0):
            for item in self.csetsList.selectedItems():
                itemIndex = self.csetsList.row(item)
                self.csetsList.takeItem(itemIndex)

    def csetsListSelectionChanged(self):
        if (len(self.csetsList.selectedItems()) > 0):
            self.animNames.clear()

            jsonTree = self.csetsList.selectedItems()[0].jsonTree

            for item in jsonTree:
                if(isParent(jsonTree[item])):
                    parentItem = AnimNamesItem(item, True, True)
                    self.animNames.addItem(parentItem)
                    for i in range(len(facing)):
                        itemToAdd = AnimNamesItem("    " + facing[i])
                        itemToAdd.setIschildof(parentItem)
                        itemToAdd.setAarray(jsonTree[item][facing[i]])
                        self.animNames.addItem(itemToAdd)
                else:
                    SingleItem = AnimNamesItem(item, False, True)
                    SingleItem.setAarray(jsonTree[item])
                    self.animNames.addItem(SingleItem)

            self.animNames.setEnabled(True)
            self.animNames.setCurrentRow(0)

    def charasetNew(self):

        self.csetsList.clear()
        self.animNames.clear()
        self.animList.clear()

    def charasetOpen(self):

        if(self.ssettings == {}):
            filepath = os.path.expanduser("~")
        else:
            if "gamefolder" in self.ssettings:
                filepath = os.path.join(
                    self.ssettings["gamefolder"], fifl.CHARASETS)

        filename = str(QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File', filepath))
        self.__charasetOpen(filename)

    def __charasetOpen(self, filename):
        if os.path.isfile(filename):
            self.csetsList.clear()
            self.animNames.clear()
            self.animList.clear()
            self.cset.load(filename)
            self.ssettings["gamefolder"] = os.path.abspath(
                os.path.join(os.path.dirname(str(filename)), "../../"))
            self.__imgOpen(os.path.join(self.ssettings[
                           "gamefolder"], fifl.IMG, self.cset.jsonTree["Charaset"]["tileImage"]))
            for charset in self.cset.jsonTree["Charaset"]:
                if(charset != "tileImage"):
                    self.csetsList.addItem(
                        csetsItem(charset, self.cset.jsonTree["Charaset"][charset]))

    def charasetSave(self):
        self.cset.new()

        self.cset.setTileImage(self.tileImage)
        for itemIndex in range(self.csetsList.count()):
            self.cset.addCharaset(str(self.csetsList.item(
                itemIndex).aname), self.csetsList.item(itemIndex).jsonTree)

        self.cset.save()

    def imgOpen(self):

        if(self.ssettings == {}):
            filepath = os.path.expanduser("~")

        filename = str(QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File', filepath))
        if os.path.isfile(filename):
            self.__imgOpen(filename)

    def __imgOpen(self, filename):
        self.palette.update(filename)
        self.palImageFile.setText(filename)

        self.animList.clear()
        self.animNames.clear()
        self.tileImage = os.path.basename(filename)

    def animNamesChanged(self, dummy):

        # print("changed!\n")
        # print(self.csetsList.selectedItems()[0].jsonTree)
        jsonTree = {}

        for iItem in range(self.animNames.count()):
            if(self.animNames.item(iItem).isparent and not self.animNames.item(iItem).isgroup):
                jsonTree[self.animNames.item(iItem).aname] = self.animNames.item(
                    iItem).getAarray()
            if(self.animNames.item(iItem).isparent and self.animNames.item(iItem).isgroup):
                jsonTree[self.animNames.item(iItem).aname] = {}
                for jItem in range(self.animNames.count()):
                    if(self.animNames.item(jItem).ischildof == self.animNames.item(iItem)):
                        animationame = self.animNames.item(iItem).aname
                        facing = self.animNames.item(jItem).aname.strip()
                        jsonTree[animationame][
                            facing] = self.animNames.item(jItem).getAarray()

        self.csetsList.selectedItems()[0].jsonTree = {}
        # print("\nto:\n")
        # print jsonTree
        self.csetsList.selectedItems()[0].jsonTree = jsonTree

    def animNamesEnable(self, dummy):
        if(len(self.animNamesEntry.text()) > 0):
            self.animNamesAdd.setEnabled(True)
            self.animNames.setEnabled(True)
        else:
            self.animNamesAdd.setEnabled(False)
            self.animNames.setEnabled(False)

    def animNamesDelAction(self):
        if (len(self.animNames.selectedItems()) > 0):
            for item in self.animNames.selectedItems():
                if(item.isparent):
                    for itemIndex in range(self.animNames.count()):
                        if(self.animNames.item(itemIndex).ischildof == item):
                            self.animNames.takeItem(itemIndex)

                    itemIndex = self.animNames.row(item)
                    self.animNames.takeItem(itemIndex)
                elif(item.ischildof):
                    itemsToTake = []
                    for itemIndex in range(self.animNames.count()):
                        if(self.animNames.item(itemIndex).ischildof == item.ischildof and self.animNames.item(itemIndex) != item):
                            itemsToTake.append(self.animNames.item(itemIndex))

                    for itemtotake in itemsToTake:
                        self.animNames.takeItem(self.animNames.row(itemtotake))

                    itemIndex = self.animNames.row(item.ischildof)
                    self.animNames.takeItem(itemIndex)

                    itemIndex = self.animNames.row(item)
                    self.animNames.takeItem(itemIndex)

        else:
            self.animNames.clear()

        self.updating = True
        self.animList.clear()
        self.animPreview.clearAnim()
        self.updating = False

        self.animNamesSelectionChanged()

    def animListDelAction(self):
        if (len(self.animList.selectedItems()) > 0):
            for item in self.animList.selectedItems():
                itemIndex = self.animList.row(item)
                self.animList.takeItem(itemIndex)
        else:
            self.animList.clear()

        self.animListUpdated()

    def animNamesSelectionChanged(self):
        self.animPreview.clearAnim()

        if (len(self.animNames.selectedItems()) > 0):
            if(self.animNames.selectedItems()[0].isgroup):
                curRow = self.animNames.currentRow()
                curRow += 1
                self.animNames.setCurrentRow(curRow)

            if(not self.animNames.selectedItems()[0].isgroup):
                animArray = self.animNames.selectedItems()[0].getAarray()
                scale = 2
                bcset = self.palette.myBC.bcset

                self.updating = True

                self.animList.clear()
                if(len(animArray) > 0):
                    for item in animArray:
                        self.animList.addItem(CsetAItem(item, bcset, 2))

                self.updating = False
                self.animPreview.setAnimArray(bcset, animArray)

    def animNamesAddAction(self):
        if(len(self.animNamesEntry.text()) > 0):
            if self.animNamesCheckBNF.isChecked():
                self.animNames.addItem(AnimNamesItem(
                    str(self.animNamesEntry.text()).strip(), False, True))
            else:
                parentItem = AnimNamesItem(
                    str(self.animNamesEntry.text()).strip(), True, True)
                self.animNames.addItem(parentItem)
                for i in range(len(facing)):
                    itemToAdd = AnimNamesItem("    " + facing[i])
                    itemToAdd.setIschildof(parentItem)
                    self.animNames.addItem(itemToAdd)

    def animselected(self):
        if (len(self.animNames.selectedItems()) > 0):
            self.animList.addItem(CsetAItem(self.palette.rValue[
                                  0], self.palette.rValue[1], self.palette.rValue[2]))
            print(self.palette.rValue[0])

    def animListUpdated(self):
        if(self.updating == False):
            if (self.animList.count() > 0):
                animArray = []
                i = 0
                while i < self.animList.count():
                    item = self.animList.item(i)
                    animArray.append(item.getCharType())
                    i += 1

                self.animPreview.setAnimArray(
                    self.palette.myBC.bcset, animArray)
                self.animNames.selectedItems()[0].setAarray(animArray)
            else:
                self.animPreview.clearAnim()
                self.animNames.selectedItems()[0].setAarray([])


class CharasPaletteWidget(QWidget):

    def __init__(self, pMap, pSettings, parent=None, **kwargs):
        super().__init__(parent, **kwargs)


class CharasEditorWidget(QWidget):

    def __init__(self, pMap, pSettings, parent=None, **kwargs):
        super().__init__(parent, **kwargs)


if __name__ == "__main__":
    from sys import argv, exit

    a = QApplication(argv)
    # m=CharasetSelector()
    m = CharasetEditorWidget()
    a.processEvents()
    m.show()
    m.raise_()
    exit(a.exec_())
