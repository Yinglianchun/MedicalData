from utils.getPublicData import getAllCasesData

# def getPieData():
#     casesList = getAllCasesData()   # 用于接收getPieData的变量
#     ageDic = {'0-10岁':0,'10-20岁':0,'20-30岁':0,'30-40岁':0,'40-50岁':0,'50-60岁':0,'60岁以上':0} # 用于计算各年龄段的数量
#     for caseItem in casesList:
#         if int(caseItem[3]) < 10:  # 先换成整型再计算
#             ageDic['0-10岁'] += 1

#         elif int(caseItem[3]) < 20:
#             ageDic['10-20岁'] += 1
#         elif int(caseItem[3]) < 30:
#             ageDic['20-30岁'] += 1
#         elif int(caseItem[3]) < 40:
#             ageDic['30-40岁'] += 1
#         elif int(caseItem[3]) < 50:
#             ageDic['40-50岁'] += 1
#         elif int(caseItem[3]) < 60:
#             ageDic['50-60岁'] += 1
#         else:
#             ageDic['60岁以上'] += 1
#     # print(ageDic)
#     listResult = []
#     for k, v in ageDic.items():
#         listResult.append({
#             'name':k,
#             'value':v
#         })
#     print(listResult)
#     return listResult
def getPieData():
    casesList = getAllCasesData()
    ageDic = {
        '0-10岁': 0,
        '10-20岁': 0,
        '20-30岁': 0,
        '30-40岁': 0,
        '40-50岁': 0,
        '50-60岁': 0,
        '60岁以上': 0,
    }
    for caseItem in casesList:
        try:
            age = int(caseItem[3])  # 年龄在第 4 列
        except (TypeError, ValueError):
            # 像“无”这类不能转成数字的，直接跳过
            continue

        if age < 10:
            ageDic['0-10岁'] += 1
        elif age < 20:
            ageDic['10-20岁'] += 1
        elif age < 30:
            ageDic['20-30岁'] += 1
        elif age < 40:
            ageDic['30-40岁'] += 1
        elif age < 50:
            ageDic['40-50岁'] += 1
        elif age < 60:
            ageDic['50-60岁'] += 1
        else:
            ageDic['60岁以上'] += 1

    listResult = []
    for k, v in ageDic.items():
        listResult.append({
            'name': k,
            'value': v
        })
    return listResult

def getConfigOne(): # 定义后端接口
    casesList = getAllCasesData() # 获取数据库数据
    caseDic = {}  # 字典 接收数据
    for caseItem in casesList:
        if caseDic.get(caseItem[1],-1) == -1:   # 通过for循环对类型进行统计 如果没有该类型字段则=-1,并赋值为1
            caseDic[caseItem[1]] = 1
        else:
            caseDic[caseItem[1]] += 1  # 有该类型字段则+1

    listResult = []
    for k, v in caseDic.items():
        listResult.append({
            'name':k,
            'value':v
        })
    # print(1,listResult)
    return listResult[:6],listResult

def getFoundData():
    casesList = getAllCasesData()
    maxNum = len(list(casesList))
    typeDic = {}
    depDic = {}
    hosDic = {}
    maxAge = 0
    minAge = 100
    for caseItem in casesList:
        # 类型
        if typeDic.get(caseItem[1],-1) == -1:
            typeDic[caseItem[1]] = 1
        else:
            typeDic[caseItem[1]] += 1
        # 科室
        if depDic.get(caseItem[8], -1) == -1:
            depDic[caseItem[8]] = 1
        else:
            depDic[caseItem[8]] += 1
        # 医院
        if hosDic.get(caseItem[7], -1) == -1:
            hosDic[caseItem[7]] = 1
        else:
            hosDic[caseItem[7]] += 1
        # 年龄
        # if int(caseItem[3]) > maxAge:
        #     maxAge = int(caseItem[3])
        # if int(caseItem[3]) < minAge:
        #     minAge = int(caseItem[3])
        try:
            age = int(caseItem[3])
        except (TypeError, ValueError):
            continue
        if age > maxAge:
            maxAge = age
        if age < minAge:
            minAge = age

    typeSort = sorted(typeDic.items(),key=lambda data: data[1], reverse=True)  # 排序
    depSort = sorted(depDic.items(), key=lambda data: data[1], reverse=True)
    hosSort = sorted(hosDic.items(), key=lambda data: data[1], reverse=True)
    maxType = typeSort[0][0]
    maxDep = depSort[0][0]
    maxHos = hosSort[0][0]
    # print(maxNum,maxType,maxDep,maxHos,maxAge,minAge)
    return maxNum,maxType,maxDep,maxHos,maxAge,minAge

def getGenderData():
    casesList = getAllCasesData()
    boyDic = {}
    girlDic = {}
    boyNum = 0
    girlNum = 0
    for caseItem in casesList:
        if caseItem[2] == '男':   # 先判断性别
            boyNum += 1
            if boyDic.get(caseItem[1],-1) ==-1:  # 再判断疾病类型
                boyDic[caseItem[1]] = 1
            else:
                boyDic[caseItem[1]] += 1
        elif caseItem[2] =='女':
            girlNum += 1
            if girlDic.get(caseItem[1],-1) == -1:
                girlDic[caseItem[1]] = 1
            else:
                girlDic[caseItem[1]] += 1
    # print(boyNum,girlNum)
    ratioData = []
    boyRatio = int(round(boyNum/len(casesList)*100,0))  # 保留一位小数点
    girlRatio = int(round(girlNum/len(casesList)*100,0))
    # print(boyRatio,girlRatio)
    ratioData.append(girlRatio)
    ratioData.append(boyRatio)

    boyList = []
    girlList = []
    for k,v in boyDic.items():
        boyList.append({
            'name':k,
            'value':v
        })
    for k,v in girlDic.items():
        girlList.append({
            'name':k,
            'value':v
        })
    return boyList,girlList,ratioData

def getCircleData():
    casesList = getAllCasesData()
    depDic = {}
    for caseItem in casesList:
        if depDic.get(caseItem[8],-1) == -1:
            depDic[caseItem[8]] = 1
        else:
            depDic[caseItem[8]] += 1
    # print(depDic)
    dataSort = sorted(depDic.items(), key=lambda data: data[1], reverse=True)  # 从高到低排序
    dataResultList = []
    for i in dataSort:
        dataResultList.append({
            'name':i[0],
            'value':i[1]
        })
    # print(dataResultList)
    return dataResultList

def getBodyData():
    casesList = getAllCasesData()
    dataDic = {}
    xData =[]  # x轴
    sumData = [] # 统计不同疾病类型的数量
    for caseItem in casesList:
        if dataDic.get(caseItem[1],-1) == -1:
            dataDic[caseItem[1]] = 1
        else:
            dataDic[caseItem[1]] += 1
    dataSort = sorted(dataDic.items(), key=lambda data: data[1], reverse=True)
    for i in dataSort:
        xData.append(i[0])
        sumData.append(i[1])
    y1Data = [0 for i in range(len(xData))] # 列表生成式获取y轴数据
    y2Data = [0 for i in range(len(xData))]
    # for caseItem in casesList:
    #    for index,x in enumerate(xData):  # 先获取数据库中的数据，再与x轴数据进行比对
    #        if caseItem[1] == x:
    #            if (caseItem[10] == '无' and caseItem[11] == '无') or (caseItem[10] is None or caseItem[11] is None):
    #                y1Data[index] += 0
    #                y2Data[index] += 0
    #            else:
    #                y1Data[index] += int(caseItem[10])
    #                y2Data[index] += int(caseItem[11])
    for caseItem in casesList:
       for index, x in enumerate(xData):
           if caseItem[1] == x:
               h = caseItem[10]
               w = caseItem[11]

               # 身高/体重为 None 或 “无” 时跳过
               if h is None or w is None:
                   continue
               if str(h) == '无' and str(w) == '无':
                   continue

               try:
                   h_int = int(h)
                   w_int = int(w)
               except (TypeError, ValueError):
                   # 出现“无”等非数字的情况，直接跳过
                   continue

               y1Data[index] += h_int
               y2Data[index] += w_int

    print(y1Data,y2Data,sumData)
    for index,sum in enumerate(sumData):
        y1Data[index] = round(y1Data[index]/sumData[index],0)
        y2Data[index] = round(y2Data[index]/sumData[index],0)
    print(y1Data,y2Data)
    return xData,y1Data,y2Data
