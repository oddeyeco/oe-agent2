last_value = {}

def storevar(mytype, myvalue):
    last_value.update({mytype:myvalue})

def getvar(mytype):
    return last_value[mytype]
