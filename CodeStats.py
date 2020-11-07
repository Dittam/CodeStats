import os
import sys
import unicodedata
import re
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import datetime


class CodeStats(object):
  """docstring for CodeStats"""

  def __init__(self, rootPaths, validExtensions, exclusions, commentSymbols):
    self.rootPaths = rootPaths
    self.validExtensions = validExtensions
    self.exclusions = exclusions
    self.commentSymbols = commentSymbols

  def _getFileInfoRecursively(self, root, fileInfo):
    # check if the root path is not an exclusion nor contins filenames or
    # directory names that are exclusions
    if not any(dirName in root for dirName in self.exclusions):
      # if root is a directory continue recursing
      try:
        dirs = os.listdir(root)
        for subdir in dirs:
          self._getFileInfoRecursively(root + "/" + subdir, fileInfo)
      # if root is a file get line counts
      except NotADirectoryError:
        fileName, fileExtension = os.path.splitext(root)
        if fileExtension in self.validExtensions:
          print(fileName)
          date = min(os.path.getctime(root), os.path.getmtime(root))
          output = [root, fileExtension, date]
          output.extend(self._getCountsPerFile(root, fileExtension))
          fileInfo.append(output)

  def _getCountsPerFile(self, pathToFile, fileExtension):
    with open(pathToFile, encoding="utf8", errors='ignore') as file:
      fileData = file.readlines()

    codeLines, commentLines, blankLines, docstringCount, numDocstrings = 0, 0, 0, 0, 0

    # Count python docstrings as comments and remove them from file
    if fileExtension == ".py":
      numDocstrings, docstringCount, fileData = self._countPythonDocstrings(
          fileData)

    for line in fileData:
      strippedLine = line.strip()
      if len(strippedLine) == 0:
        blankLines += 1
      elif strippedLine.startswith(self.commentSymbols):
        commentLines += 1
      else:
        codeLines += 1
    # substract numDocStrings since re.sub adds extra blank lines
    return [codeLines, commentLines + docstringCount, blankLines - numDocstrings]

  def _countPythonDocstrings(self, fileData):
    """Counts number of lines in python docstrings and removes them from the file
    """
    fileData = "".join(fileData)
    regex = "('''[\s\S]*?''')|(\"\"\"[\s\S]*?\"\"\")"

    docstrings = []
    for i in re.findall(regex, fileData):
      # append matched strign from first regex group
      if i[0]:
        docstrings.append(i[0])
      # append matched strign from second regex group
      elif i[1]:
        docstrings.append(i[1])

    numDocstrings = len(docstrings)
    docstringCount = 0  # number of lines in all docstrings in file
    for doc in docstrings:
      docstringCount += len(doc.split("\n"))
    dataDocsRemoved = re.sub(regex, "", fileData)
    return numDocstrings, docstringCount, dataDocsRemoved.split("\n")

  def generateFileStats(self):
    fileInfo = []
    for root in self.rootPaths:
      self._getFileInfoRecursively(root, fileInfo)

    fileStatsDF = pd.DataFrame(fileInfo, columns=["fileName", "fileExtension",
                                                  "dateCreated", "codeCount",
                                                  "commentCount", "blankCount"])
    fileStatsDF["codeCount"] = fileStatsDF["codeCount"].astype(int)
    fileStatsDF["commentCount"] = fileStatsDF["commentCount"].astype(int)
    fileStatsDF["blankCount"] = fileStatsDF["blankCount"].astype(int)
    fileStatsDF["dateCreated"] = fileStatsDF["dateCreated"].astype(float)
    fileStatsDF["dateCreated"] = fileStatsDF["dateCreated"].apply(
        lambda x: datetime.datetime.utcfromtimestamp(x).strftime('%Y-%m'))
    return fileStatsDF

  def visualizeCountsByExtensionType(self, fileStatsDF):
    # filter fileStatsDF by fileExtensions and sum lineCounts
    temp = fileStatsDF[["fileExtension", "codeCount", "commentCount",
                        "blankCount"]].groupby("fileExtension").sum().reset_index()

    subTotal = (temp["codeCount"].sum(), temp[
                "commentCount"].sum(), temp["blankCount"].sum())

    total = "Total lines: {}".format(temp["codeCount"].sum(
    ) + temp["commentCount"].sum() + temp["blankCount"].sum())

    temp["extenTypeTotals"] = temp.sum(axis=1)
    temp = temp.sort_values(by=["extenTypeTotals"], ascending=False)

    #------graph customization------
    fig = plt.figure(facecolor='#07000d')
    fig.canvas.set_window_title('Line Counts')
    ax1 = fig.add_subplot(1, 1, 1, facecolor='#07000d')
    ax1.axis("equal")
    plt.rcParams['savefig.facecolor'] = '#07000d'
    plt.rcParams['text.color'] = '#ffffff'
    plt.rcParams['font.size'] = 14
    colors = ['#b3daff', '#99ceff', '#80c1ff', '#66b5ff', '#4da9ff', '#339cff',
              '#1a90ff', '#0084ff', '#0077e6', '#0069cc', '#005cb3', '#004f99',
              '#004280', '#003566', '#00284d']
    wedges, texts = ax1.pie(list(temp["extenTypeTotals"]), startangle=90,
                            labels=list(temp["fileExtension"]), colors=colors)

    for w in wedges:
      w.set_linewidth(3)
      w.set_edgecolor('#07000d')

    legendLabel = ["{} {}".format(list(temp["fileExtension"])[i], list(
        temp["extenTypeTotals"])[i]) for i in range(len(list(temp["fileExtension"])))]

    plt.legend(facecolor='#07000d', labels=legendLabel,
               loc='upper right', bbox_to_anchor=(0.25, 1.0))

    titleObj = plt.title('Total Line Counts by File Type ' +
                         datetime.datetime.now().strftime("%B %d, %Y"))
    plt.getp(titleObj)  # print out the properties of title
    plt.getp(titleObj, 'text')  # print out the 'text' property for title
    plt.setp(titleObj, color='#ffffff')
    ax1.text(-2.0125, -0.05,
             "Total code lines: {}".format(subTotal[0]), fontsize=15, color='white')
    ax1.text(-2.0125, -0.12,
             "Total comment lines: {}".format(subTotal[1]), fontsize=15, color='white')
    ax1.text(-2.0125, -0.19,
             "Total blank lines: {}".format(subTotal[2]), fontsize=15, color='white')
    ax1.text(-2.0125, -0.26, total, fontsize=15, color='white')

  def visualizeCountsOvertime(self, fileStatsDF):
    temp = fileStatsDF.groupby(
        ["dateCreated", "fileExtension"]).sum().reset_index()
    temp["totalLineCount"] = temp.sum(axis=1)
    pivot = temp.pivot_table(
        index='dateCreated', columns='fileExtension', values='totalLineCount')

    #------graph customization------
    colors = ["#f5f0ce", "#31A354", "#ff0000", "#ffff66", "#0066ff", "#74C476",
              "#6600cc", '#f4b642', "#ff00ff", "#ff9999", "#660033", '#41f1f4',
              '#41ebf4', '#7cf441', '#f4cd41']
    fig2 = plt.figure(facecolor='#07000d')
    fig2.canvas.set_window_title(
        'Line Count Distribution by Month and File Type')
    ax2 = fig2.add_subplot(1, 1, 1, facecolor='#07000d')
    plt.rcParams['savefig.facecolor'] = '#07000d'
    # ax2.set_ylim([0, 9000])
    plt.ylabel('Messages', color='#ffffff')
    ax2.tick_params(axis='y', colors='#ffffff')
    ax2.tick_params(axis='x', colors='#ffffff')
    ax2.spines['bottom'].set_color('#5998ff')
    ax2.spines['left'].set_color('#5998ff')
    ax2.spines['right'].set_color('#5998ff')
    ax2.spines['top'].set_color('#5998ff')
    ax2.grid(True, color='#ffffff', alpha=0.3, linewidth=0.4)

    pivot.plot.bar(stacked=True, color=colors,
                   figsize=(10, 7), ax=ax2, grid=True, alpha=0.7, linewidth=0.8,
                   edgecolor='#5998ff', rot=-65)

    title_obj = plt.title('Line Count Distribution by Month and File Type ' +
                          datetime.datetime.now().strftime("%B %d, %Y"))
    plt.getp(title_obj)  # print out the properties of title
    plt.getp(title_obj, 'text')  # print out the 'text' property for title
    plt.setp(title_obj, color='#ffffff')
    for text in plt.legend(framealpha=0, loc='best').get_texts():
      plt.setp(text, color='w')

  def visualizeFileCounts(self, fileStatsDF):
    # filter fileStatsDF by fileExtensions and sum lineCounts
    temp = fileStatsDF[["fileName", "fileExtension"]
                       ].groupby("fileExtension").count()
    temp.columns = ["fileCount"]
    temp = temp.sort_values("fileCount", ascending=False)
    total = "Total: " + str(temp["fileCount"].sum())

    #------graph customization------
    fig3 = plt.figure(facecolor='#07000d')
    fig3.canvas.set_window_title('File Counts')
    ax3 = fig3.add_subplot(1, 1, 1, facecolor='#07000d')
    ax3.axis("equal")
    plt.rcParams['savefig.facecolor'] = '#07000d'
    plt.rcParams['text.color'] = '#ffffff'
    plt.rcParams['font.size'] = 14
    colors = ['#b3daff', '#99ceff', '#80c1ff', '#66b5ff', '#4da9ff', '#339cff',
              '#1a90ff', '#0084ff', '#0077e6', '#0069cc', '#005cb3', '#004f99',
              '#004280', '#003566', '#00284d']

    wedges, texts = ax3.pie(list(temp["fileCount"]), startangle=90,
                            labels=list(temp.index), colors=colors)

    for w in wedges:
      w.set_linewidth(3)
      w.set_edgecolor('#07000d')

    legendLabel = ["{} {}".format(list(temp.index)[i], list(
        temp["fileCount"])[i]) for i in range(len(list(temp.index)))]

    plt.legend(facecolor='#07000d', labels=legendLabel,
               loc='upper right', bbox_to_anchor=(0.25, 1.0))

    titleObj = plt.title('File Counts by Type ' +
                         datetime.datetime.now().strftime("%B %d, %Y"))
    plt.getp(titleObj)  # print out the properties of title
    plt.getp(titleObj, 'text')  # print out the 'text' property for title
    plt.setp(titleObj, color='#ffffff')
    ax3.text(-1.75, -0.005, total, fontsize=15, color='white')

if __name__ == '__main__':
  validExtensions = [".py", ".java", ".test", ".R", ".Rmd",
                     ".c", ".sh", ".h", ".css", ".html", ".tex",
                                  ".js", ".jsx", ".yml"]

  exclusions = ["__pycache__", ".git", ".ipynb_checkpoints", "node_modules", "venv",
                "C:/Users/ditta/OneDrive/Python Projects/Machine Learning Projects/Real-Time-Object-Detection/TensorFlowDetectionAPI",
                "C:/Users/ditta/OneDrive/CSCC11/Assignment3/data/cifar-10-batches-py/readme.html",
                "DittamDey.html",
                "C:/Users/ditta/OneDrive/Python Projects/SkedgeSurvey/index.html"]

  commentSymbols = ("#", "//", "/**", "*")

  roots = ["C:/Users/ditta/OneDrive", "C:/Users/ditta/Documents/Code",
           "C:/Users/ditta/Documents/Python Projects"]

  codeStats = CodeStats(roots, validExtensions, exclusions, commentSymbols)

  # generate dataframe of file info
  fileStatsDF = codeStats.generateFileStats()

  # visualize generated dataframe
  codeStats.visualizeCountsByExtensionType(fileStatsDF)
  codeStats.visualizeCountsOvertime(fileStatsDF)
  codeStats.visualizeFileCounts(fileStatsDF)
  plt.show()
