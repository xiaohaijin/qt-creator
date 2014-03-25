#############################################################################
##
## Copyright (C) 2014 Digia Plc and/or its subsidiary(-ies).
## Contact: http://www.qt-project.org/legal
##
## This file is part of Qt Creator.
##
## Commercial License Usage
## Licensees holding valid commercial Qt licenses may use this file in
## accordance with the commercial license agreement provided with the
## Software or, alternatively, in accordance with the terms contained in
## a written agreement between you and Digia.  For licensing terms and
## conditions see http://qt.digia.com/licensing.  For further information
## use the contact form at http://qt.digia.com/contact-us.
##
## GNU Lesser General Public License Usage
## Alternatively, this file may be used under the terms of the GNU Lesser
## General Public License version 2.1 as published by the Free Software
## Foundation and appearing in the file LICENSE.LGPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU Lesser General Public License version 2.1 requirements
## will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
##
## In addition, as a special exception, Digia gives you certain additional
## rights.  These rights are described in the Digia Qt LGPL Exception
## version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
##
#############################################################################

source("../../shared/qtcreator.py")

# necessary to not use symbolic links for the parent path of the git project
srcPath = os.path.realpath(srcPath)
projectName = "gitProject"

# TODO: Make selecting changes possible
def commit(commitMessage, expectedLogMessage):
    openVcsLog()
    clickButton(waitForObject(":*Qt Creator.Clear_QToolButton"))
    invokeMenuItem("Tools", "Git", "Local Repository", "Commit...")
    replaceEditorContent(waitForObject(":Description.description_Utils::CompletingTextEdit"), commitMessage)
    ensureChecked(waitForObject(":Files.Check all_QCheckBox"))
    checkOrFixCommitterInformation('invalidAuthorLabel', 'authorLineEdit', 'Nobody')
    checkOrFixCommitterInformation('invalidEmailLabel', 'emailLineEdit', 'nobody@nowhere.com')
    clickButton(waitForObject(":splitter.Commit File(s)_VcsBase::QActionPushButton"))
    vcsLog = waitForObject("{type='QPlainTextEdit' unnamed='1' visible='1' "
                           "window=':Qt Creator_Core::Internal::MainWindow'}").plainText
    test.verify(expectedLogMessage in str(vcsLog), "Searching for '%s' in log:\n%s " % (expectedLogMessage, vcsLog))
    return commitMessage

def verifyItemsInGit(commitMessages):
    gitEditor = waitForObject(":Qt Creator_Git::Internal::GitEditor")
    waitFor("str(gitEditor.plainText) != 'Waiting for data...'", 20000)
    plainText = str(gitEditor.plainText)
    verifyItemOrder(commitMessages, plainText)
    return plainText

def createLocalGitConfig(path):
    config = os.path.join(path, "config")
    test.verify(os.path.exists(config), "Verifying if .git/config exists.")
    file = open(config, "a")
    file.write("\n[user]\n\temail = nobody@nowhere.com\n\tname = Nobody\n")
    file.close()

def checkOrFixCommitterInformation(labelName, lineEditName, expected):
    lineEd = waitForObject("{name='%s' type='QLineEdit' visible='1'}" % lineEditName)
    if not (test.compare(lineEd.text, expected, "Verifying commit information matches local config")
        and test.verify(checkIfObjectExists("{name='%s' type='QLabel' visible='1'}" % labelName,
                                            False, 1000),
                                            "Verifying invalid label is missing")):
        test.log("Commit information invalid or missing - entering dummy value (%s)" % expected)
        replaceEditorContent(lineEd, expected)

def verifyClickCommit():
    gitEditor = waitForObject(":Qt Creator_Git::Internal::GitEditor")
    fileName = waitForObject(":Qt Creator_FilenameQComboBox")
    test.verify(waitFor('str(fileName.currentText).startswith("Git Log")', 1000),
                "Verifying Qt Creator still displays git log inside editor.")
    content = str(gitEditor.plainText)
    noOfCommits = content.count("commit")
    commit = None
    # find second commit
    try:
        line = filter(lambda line: line.startswith("commit"), content.splitlines())[-2]
        commit = line.split(" ", 1)[1]
    except:
        test.fail("Could not find the second commit - leaving test")
        return
    placeCursorToLine(gitEditor, line)
    for i in range(5):
        type(gitEditor, "<Left>")
    # get the current cursor rectangle which should be positioned on the commit ID
    rect = gitEditor.cursorRect()
    # click on the commit ID
    mouseClick(gitEditor, rect.x, rect.y + rect.height / 2, 0, Qt.LeftButton)
    expected = 'Git Show "%s"' % commit
    test.verify(waitFor('str(fileName.currentText) == expected', 5000),
                "Verifying editor switches to Git Show.")
    diffShow = waitForObject(":Qt Creator_DiffEditor::Internal::DescriptionEditorWidget")
    waitFor('len(str(diffShow.plainText)) != 0', 5000)
    show = str(diffShow.plainText)
    expected = [{"commit %s" % commit:False},
                {"Author: Nobody <nobody@nowhere.com>": False},
                {"Date:\s+\w{3} \w{3} \d{1,2} \d{2}:\d{2}:\d{2} \d{4}.*":True}]
    for line, exp in zip(show.splitlines(), expected):
        expLine = exp.keys()[0]
        isRegex = exp.values()[0]
        if isRegex:
            test.verify(re.match(expLine, line), "Verifying commit header line '%s'" % line)
        else:
            test.compare(line, expLine, "Verifying commit header line.")
    changed = waitForObject(":Qt Creator_DiffEditor::SideDiffEditorWidget")
    original = waitForObject(":Qt Creator_DiffEditor::SideDiffEditorWidget2")
    waitFor('str(changed.plainText) != "Waiting for data..." '
            'and str(original.plainText) != "Waiting for data..."', 5000)
    # content of diff editors is merge of modified files
    diffOriginal = str(original.plainText)
    diffChanged = str(changed.plainText)
    # diffChanged must completely contain the pointless_header.h
    pointlessHeader = readFile(os.path.join(srcPath, projectName, "pointless_header.h"))
    test.verify(pointlessHeader in diffChanged,
                "Verifying whether diff editor contains pointless_header.h file.")
    test.verify(pointlessHeader not in diffOriginal,
                "Verifying whether original does not contain pointless_header.h file.")
    test.verify("HEADERS  += mainwindow.h \\\n    pointless_header.h\n" in diffChanged,
                "Verifying whether diff editor has pointless_header.h listed in pro file.")
    test.verify("HEADERS  += mainwindow.h\n\n" in diffOriginal
                and "pointless_header.h" not in diffOriginal,
                "Verifying whether original has no additional header in pro file.")
    test.verify(original.readOnly and changed.readOnly and diffShow.readOnly,
                "Verifying all diff editor widgets are readonly.")

def main():
    startApplication("qtcreator" + SettingsPath)
    if not startedWithoutPluginError():
        return
    createProject_Qt_GUI(srcPath, projectName, addToVersionControl = "Git")
    openVcsLog()
    vcsLog = waitForObject("{type='QPlainTextEdit' unnamed='1' visible='1' "
                           "window=':Qt Creator_Core::Internal::MainWindow'}").plainText
    test.verify("Initialized empty Git repository in %s"
                % os.path.join(srcPath, projectName, ".git").replace("\\", "/") in str(vcsLog),
                "Has initialization of repo been logged:\n%s " % vcsLog)
    createLocalGitConfig(os.path.join(srcPath, projectName, ".git"))
    commitMessages = [commit("Initial Commit", "Committed 5 file(s).")]
    clickButton(waitForObject(":*Qt Creator.Clear_QToolButton"))
    addCPlusPlusFileToCurrentProject("pointless_header.h", "C++ Header File", addToVCS = "Git")
    commitMessages.insert(0, commit("Added pointless header file", "Committed 2 file(s)."))
    __createProjectOrFileSelectType__("  General", "Text File", isProject=False)
    readmeName = "README"
    replaceEditorContent(waitForObject(":New Text File.nameLineEdit_Utils::FileNameValidatingLineEdit"), readmeName)
    clickButton(waitForObject(":Next_QPushButton"))
    readmeName += ".txt"
    __createProjectHandleLastPage__([readmeName], "Git", "<None>")
    replaceEditorContent(waitForObject(":Qt Creator_TextEditor::PlainTextEditorWidget"),
                         "Some important advice in the README")
    invokeMenuItem("File", "Save All")
    commitsInProject = list(commitMessages) # deep copy
    commitOutsideProject = commit("Added README file", "Committed 2 file(s).") # QTCREATORBUG-11074
    commitMessages.insert(0, commitOutsideProject)

    invokeMenuItem('Tools', 'Git', 'Current File', 'Log of "%s"' % readmeName)
    fileLog = verifyItemsInGit([commitOutsideProject])
    for commitMessage in commitsInProject:
        test.verify(not commitMessage in fileLog,
                    "Verify that no unrelated commits are displayed in file log")
    invokeMenuItem("File", "Close All")

    invokeMenuItem('Tools', 'Git', 'Current Project', 'Log Project "%s"' % projectName)
    projectLog = verifyItemsInGit(commitsInProject)
    test.xverify(not commitOutsideProject in projectLog,    # QTCREATORBUG-10170
                 "Verify that no unrelated commits are displayed in project log")
    invokeMenuItem("File", "Close All")

    invokeMenuItem("Tools", "Git", "Local Repository", "Log")
    verifyItemsInGit(commitMessages)
    # verifyClickCommit() must be called after the local git has been created and the files
    # have been pushed to the repository
    verifyClickCommit()
    invokeMenuItem("File", "Close All Projects and Editors")

    invokeMenuItem("File", "Exit")

def deleteProject():
    path = os.path.join(srcPath, projectName)
    if os.path.exists(path):
        try:
            # Make files in .git writable to remove them
            for root, dirs, files in os.walk(path):
                for name in files:
                    os.chmod(os.path.join(root, name), stat.S_IWUSR)
            shutil.rmtree(path)
        except:
            test.warning("Error while removing '%s'" % path)

def init():
    deleteProject()

def cleanup():
    deleteProject()
