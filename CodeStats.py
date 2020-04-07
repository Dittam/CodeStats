import os
import sys
import unicodedata
import re
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import datetime


def getLineCountPerFile(pathToFile):
    with open(pathToFile, encoding="utf8", errors='ignore') as file:
        data = file.readlines()
        return len(data)


def getCommentCountPerFile(pathToFile):
    with open(pathToFile, encoding="utf8", errors='ignore') as file:
        data = file.readlines()
        c = 0
        for line in data:
            if len(line.replace(" ", "")) > 1:
                if line.replace(" ", "")[0] == "#" or line.replace(" ", "")[
                        0] == "//" or line.replace(" ", "")[
                        0] == "*":
                    c += 1

        return c


def getFilePathsRecursively(curPath, output):
    if any(x in curPath for x in validExtensions) and not any(
            x in curPath for x in invalidExtensions) and not any(
            x in curPath for x in fileExclusions):
        output.append(curPath)
    elif not any(x in curPath for x in directoryExclusions):
        try:  # handle files without extensions e.g. makefile
            curList = os.listdir(curPath)
            for element in curList:
                getFilePathsRecursively(curPath + "/" + element, output)
        except NotADirectoryError as e:
            pass


def generateStatsDataframe(rootDirectory):
    filePaths, date, exten, lineCounts, commentCounts = [], [], [], [], []
    for path in rootDirectory:
        getFilePathsRecursively(path, filePaths)

    for file in filePaths:
        idx = re.search("\.[a-zA-Z0-9]+$", file)
        exten.append(file[idx.start():idx.end()])
        date.append(min(os.path.getctime(file), os.path.getmtime(file)))
        lineCounts.append(getLineCountPerFile(file))
        commentCounts.append(getCommentCountPerFile(file))

    df = pd.DataFrame(np.array([date, exten, lineCounts, commentCounts]).T,
                      columns=["dateCreated", "fileExtension", "lineCount", "commentCount"])
    df["lineCount"] = df["lineCount"].astype(int)
    df["commentCount"] = df["commentCount"].astype(int)
    df["dateCreated"] = df["dateCreated"].astype(float)
    df["dateCreated"] = df["dateCreated"].apply(
        lambda x: datetime.datetime.utcfromtimestamp(x).strftime('%Y-%m'))
    return df


def generateCountsByType(df):
    # filter df by fileExtensions and sum lineCounts
    temp = df.iloc[:, 1:4].groupby("fileExtension").sum().reset_index()
    # add total comment count to temp
    temp = temp.append(pd.DataFrame({"lineCount": [df["commentCount"].sum()],
                                     "commentCount": [-1], "fileExtension": [
        "Comments"]})).sort_values(by=["lineCount"],
                                   ascending=False)
    total = "Total: " + str(df["lineCount"].sum() + df["commentCount"].sum())
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

    wedges, texts = ax1.pie(list(temp["lineCount"]), startangle=90,
                            labels=list(temp["fileExtension"]), colors=colors)

    for w in wedges:
        w.set_linewidth(3)
        w.set_edgecolor('#07000d')

    legendLabel = ["{} {}".format(list(temp["fileExtension"])[i], list(
        temp["lineCount"])[i]) for i in range(len(list(temp["fileExtension"])))]

    plt.legend(facecolor='#07000d', labels=legendLabel,
               loc='upper right', bbox_to_anchor=(0.25, 1.0))

    titleObj = plt.title('Line Counts by Type ' +
                         datetime.datetime.now().strftime("%B %d, %Y"))
    plt.getp(titleObj)  # print out the properties of title
    plt.getp(titleObj, 'text')  # print out the 'text' property for title
    plt.setp(titleObj, color='#ffffff')
    ax1.text(-2.0125, -0.05, total, fontsize=15, color='white')


def generateCountsOvertime(df):

    temp = df.groupby(["dateCreated", "fileExtension"]).sum().reset_index()
    temp2 = df[["dateCreated", "commentCount"]].groupby(
        by="dateCreated").sum().reset_index()
    temp2.columns = ["dateCreated", "lineCount"]
    temp2["fileExtension"] = "Comments"
    temp3 = pd.concat([temp, temp2])
    pivot = temp3.pivot_table(
        index='dateCreated', columns='fileExtension', values='lineCount')

    #------graph customization------
    colors = ["#f5f0ce", "#31A354", "#ff0000", "#ffff66", "#0066ff", "#74C476",
              "#6600cc", '#f4b642', "#ff00ff", "#ff9999", "#660033", '#41f1f4',
              '#41ebf4', '#7cf441', '#f4cd41']
    fig2 = plt.figure(facecolor='#07000d')
    fig2.canvas.set_window_title('Line Count Distribution by Month')
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

    title_obj = plt.title('Line Count Distribution by Month ' +
                          datetime.datetime.now().strftime("%B %d, %Y"))
    plt.getp(title_obj)  # print out the properties of title
    plt.getp(title_obj, 'text')  # print out the 'text' property for title
    plt.setp(title_obj, color='#ffffff')
    for text in plt.legend(framealpha=0, loc='best').get_texts():
        plt.setp(text, color='w')


def generatefileCounts(df):
    # filter df by fileExtensions and sum lineCounts
    temp = df.iloc[:, 1:3].groupby("fileExtension").count().reset_index()
    temp.columns = ["fileExtension", "fileCount"]
    temp = temp.sort_values(by="fileCount", ascending=False)
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
                            labels=list(temp["fileExtension"]), colors=colors)

    for w in wedges:
        w.set_linewidth(3)
        w.set_edgecolor('#07000d')

    legendLabel = ["{} {}".format(list(temp["fileExtension"])[i], list(
        temp["fileCount"])[i]) for i in range(len(list(temp["fileExtension"])))]

    plt.legend(facecolor='#07000d', labels=legendLabel,
               loc='upper right', bbox_to_anchor=(0.25, 1.0))

    titleObj = plt.title('File Counts by Type ' +
                         datetime.datetime.now().strftime("%B %d, %Y"))
    plt.getp(titleObj)  # print out the properties of title
    plt.getp(titleObj, 'text')  # print out the 'text' property for title
    plt.setp(titleObj, color='#ffffff')
    ax3.text(-1.75, -0.005, total, fontsize=15, color='white')


if __name__ == '__main__':
    validExtensions = [".py", ".java", ".test", ".R",
                       ".Rmd", ".c", ".sh", ".h", ".css", ".html", ".tex"]
    invalidExtensions = [".pyc", ".class", "h5",
                         ".config", ".csv", ".reg", "cvs", ".user", "RData", ".Rhistory"]
    directoryExclusions = [".",
                           "C:/Users/ditta/OneDrive/Python Projects/Machine Learning Projects/Real-Time-Object-Detection/TensorFlowDetectionAPI"]
    fileExclusions = [
        "C:/Users/ditta/OneDrive/CSCC11/Assignment3/data/cifar-10-batches-py/readme.html",
        "DittamDey.html",
        "C:/Users/ditta/OneDrive/Python Projects/SkedgeSurvey/index.html"]

    rootDirectory = ["C:/Users/ditta/OneDrive"]
    df = generateStatsDataframe(rootDirectory)
    generateCountsByType(df)
    generateCountsOvertime(df)
    generatefileCounts(df)
    plt.show()
    # df = pd.DataFrame(pd.date_range('2000-01-02', freq='1D', periods=15), columns=['Date'])
    # pd.set_option('display.float_format', lambda x: '%.0f' % x)
