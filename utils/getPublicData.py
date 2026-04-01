from utils.query import querys

def getAllCasesData():
    allCasesData = querys('select * from cases',[],'select')
    return allCasesData   # 获取数据库中的数据
