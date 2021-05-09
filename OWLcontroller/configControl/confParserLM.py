# config parser for the Legacy Mode
from configparser import ConfigParser
from configControl.confFile import * # TODO: need ot change this to regualr import because we want to use the name of the class and than the name of the operation , for example : controlPC.function , that way we can see it very natural the functiom and who does them
from collections import namedtuple
from collections import OrderedDict
import json
import os


# Legacy mode
#ROOT_FOLDER = r'..\\' # when running from confParser
ROOT_FOLDER = "" # when running from controlPc
LEGACY_MODE_CONF_SUFFIX = 'ini'
DEFAULT_CONF_FILE_PATH = ROOT_FOLDER + 'defaultConfiguration.json'
SEQUANCE_FILE = 'sequancefile'




def convertToString(line):
    return str(line)

def getFilePath(legacyModeConfigFilesDirectory, filename):
    return os.path.join(legacyModeConfigFilesDirectory, filename)

def getRootDirectory(relativePath):
    return r'..\\' + relativePath



def findFile(fileNameFromUser ="../"):
    path = ROOT_FOLDER + fileNameFromUser
    return path if os.path.isfile(path) else ''

# def searchFromRoot(dirNameFromUser):
#     start = "../"
#     for dirpath, dirnames, filenames in os.walk(start):
#         for filename in filenames:
#             if filename == dirNameFromUser:
#                 filename = os.path.join(dirpath, filename)
#                 # print(filename)
#                 # print(dirpath)
#                 # print(dirnames)
#                 #print(dirpath)
#                 return filename


def findDir(dirNameFromUser):
    path = ROOT_FOLDER + dirNameFromUser
    return path if os.path.isdir(path) else ''



# Parser
class confParserLM():
    def __init__(self,defaultConfContent):
        # Legacy Mode configs paths
        #TODO : first line here works, but variable isnt in use, second one dosnt work and the var is in use ... see whats up with this
        self.legacyModeConfigFilesDirectory = getRootDirectory(defaultConfContent['legacyModePath'])
        self.lMConfFilesDirectory = findDir(defaultConfContent['legacyModePath']) # LM - Legacy Mode config files directory

    # Legacy mode

    def getFilesNames(self, path):
        return os.listdir(path)

    def getGroupOfSection(self, sectionName):
        return (sectionName.split('/')[1])

    def getParamsFromSection(self, sectionName):
        return list(self.lMConfFile[sectionName])

    def getparamValue(self, sectionName, param):
        return self.lMConfFile[sectionName][param]

    def insertGroupTotestsByGroup(self, groupName, testsByGroupLM):
        if groupName not in testsByGroupLM: testsByGroupLM[groupName] = []
        return testsByGroupLM

    def addValueToLegacyConfiguration(self, testConf, Param, sectionName):
        setattr(testConf, Param, self.getparamValue(sectionName, Param))
        return testConf

    def getCurrPath(self):
        return os.getcwd().strip()

    def parseSequanceFile(self, sectionName,controlPc):
        try:
            flowOperationsFile = open((findFile(self.getparamValue(sectionName, 'sequancefile'))), encoding="utf8")
            FlowOperations = json.load(flowOperationsFile)
            flowOperationsFile.close()
        except Exception as e:
            sequenceFileName = self.getparamValue(sectionName,'sequancefile').strip()
            sequenceFileInvalidSyntaxDescription = str("The system detected an invalid syntax in the following Json file: \n" + self.getCurrPath() + '\\' + sequenceFileName + "\nPlease fix the file's content according to the following error message \n" + str(e) + "\n \n ")
            if "corruptedSequenceFile" not in controlPc.preRunValidationErorrs.keys():
                controlPc.preRunValidationErorrs["corruptedSequenceFile"] = []
                controlPc.preRunValidationErorrs["corruptedSequenceFile"].append({sequenceFileName :sequenceFileInvalidSyntaxDescription})
            else:
                for corruptedSequenceFileDict in controlPc.preRunValidationErorrs['corruptedSequenceFile']:
                    if sequenceFileName in corruptedSequenceFileDict:
                        break
                else:
                    controlPc.preRunValidationErorrs["corruptedSequenceFile"].append({sequenceFileName: sequenceFileInvalidSyntaxDescription})

                #controlPc.preRunValidationErorrs.append(sequenceFileInvalidSyntaxDescription)
            return False # When the sequence file is corrupted we are sending a "False" boolean in order to indicate this
        return FlowOperations #Otherwise we are sending the loaded json file

    def createSequanceFileConf(self, sectionName,controlPc):
        testConfiguration = testConfLegacySequenceFlow()
        sequenceFile = self.parseSequanceFile(sectionName,controlPc)
        if sequenceFile == False: #TODO change all this sequance = file dependices to work with sequancefile = None
            return False
        testConfiguration.flowoperations = []
        for operation in sequenceFile['operationsList']:
            testConfiguration.flowoperations.append(operation)
        return testConfiguration

    def addingParamsToConf(self, sectionParams,testConf,sectionName):

        for Param in sectionParams:
            testConf = self.addValueToLegacyConfiguration(testConf, Param, sectionName)
        return testConf

    def saveConfIntoDicts(self, sectionName, legacyFlowOperationsTestsByGroups, testConf):
        groupName = self.getGroupOfSection(sectionName)
        legacyFlowOperationsTestsByGroups = self.insertGroupTotestsByGroup(groupName, legacyFlowOperationsTestsByGroups)
        legacyFlowOperationsTestsByGroups[groupName].append(testConf)

    def parseLMConf(self, controlPc):
        ''' parsing Legacy mode config files '''
        legacyTestsByGroup = OrderedDict()
        legacyFlowOperationsTestsByGroups = OrderedDict()
        parseResults = namedtuple('parsingResult', ['legacyTestsByGroup',  'legacyFlowOperationsTestsByGroups' , 'indicatorForInvalidJsonFile'])
        indicatorForInvalidJsonFile = False # Used as a flag that pointing whether there's a corrupted sequence file

        # Legacy mode config file (contains sections , each section is a summary for one test)
        for filename in self.getFilesNames(self.lMConfFilesDirectory):
            if filename.endswith(LEGACY_MODE_CONF_SUFFIX):
                self.lMConfFile = ConfigParser() # TODO: legacyConfigFile is attribute that we need only for this function andd not for all the class , so need to change this to be local to the function and if oter functions usess it ned to send it to them
                self.lMConfFile.read(getFilePath(self.lMConfFilesDirectory, filename))  # (os.path.join(self.legacyModeConfigFilesDirectory, filename))
                # create configuration file
                for sectionName in self.lMConfFile.sections():
                    sectionParams = self.getParamsFromSection(sectionName)
                    if SEQUANCE_FILE in sectionParams: #TODO: "sequanceFile" should be constant , we need create a class of CONSTANTS , that way each const will be reached by const.legacy.something
                        testConf = self.createSequanceFileConf(sectionName,controlPc)
                        if testConf == False: #TODO change the name to jsonFileInvalidIndicator
                            indicatorForInvalidJsonFile = True
                            continue # If the user provided an invalid Json file (sequence file) , the system won't take it.
                           #TODO need to test why validator is crashing if we are not blocking it when the indicatorForInvalidJsonFile is True , this code should work without the indicatorForInvalidJsonFile but it doesnt , need to check why
                        self.addingParamsToConf(sectionParams,testConf, sectionName)
                        self.saveConfIntoDicts(sectionName, legacyFlowOperationsTestsByGroups, testConf)
                    else:
                        testConf = testConfLegacy()  # Creates Legacy config file container
                        self.addingParamsToConf(sectionParams, testConf, sectionName)
                        self.saveConfIntoDicts(sectionName, legacyTestsByGroup, testConf)

        return parseResults(legacyTestsByGroup, legacyFlowOperationsTestsByGroups,indicatorForInvalidJsonFile)  # return the namedTuple contains both results dicts




