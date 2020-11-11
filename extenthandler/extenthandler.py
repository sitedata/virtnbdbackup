class Extent(object):
    def __init__(self):
        self.data = False
        self.zero = False
        self.length = 0
        self.offset = 0

class ExtentHandler(object):

    """Docstring for ExtentHanlder. """

    def __init__(self, nbdFh, metaContext="base:allocation"):
        """TODO: to be defined.

        :nbdFh: TODO

        """
        self._nbdFh = nbdFh
        self._extentEntries = []
        self._metaContext = metaContext
        self._maxRequestBlock = 4294967295
        self._align = 512

    def _getExtentCallback(self, metacontext, offset, entries, status):
        if metacontext != self._metaContext:
            return
        self._extentEntries.append(entries)

    def _setRequestAligment(self):
        align = self._nbdFh.get_block_size(0)
        if align == 0:
            align = self._align
        return self._maxRequestBlock - align + 1

    def queryExtents(self):
        maxRequestLen = self._setRequestAligment()
        offset = 0
        size = self._nbdFh.get_size()
        print(size)
        while offset < size:
            request_length = min(size - offset, maxRequestLen)
            self._nbdFh.block_status(request_length, offset, self._getExtentCallback)
            offset+=request_length

        ct = 0
        while ct<len(self._extentEntries):
            last = ct-1
            if last < 0 or ct == 0:
                pass
            else:
                last_size = self._extentEntries[last][-2]
                last_type = self._extentEntries[last][-1]
                curr_size = self._extentEntries[ct][0]
                curr_type = self._extentEntries[ct][1]

                # TODO: what if the types of the extents
                # do not match?
                if curr_type != last_type:
                    pass

                # now remove the last entry of the previously
                # processed block
                self._extentEntries[last].pop()
                self._extentEntries[last].pop()

                # and set the first entry of the current block
                # to the coalesced size
                self._extentEntries[ct][0] = last_size+curr_size
            ct+=1

        return self._extentEntries

    def queryBlockStatus(self, extentList=None):
        if extentList == None:
            self.queryExtents()

        if len(self._extentEntries) < 1:
            return None

        extentList = []
        startCt = 0
        for entry in self._extentEntries:
            extentType = entry[1::2]
            extentLength = entry[0::2]

            ct=0
            if startCt == 0:
                start=0
            else:
                start=startCt

            for ct in range(0,int(len(entry)/2)):
                extObj = Extent()
                assert extentType[ct] in (0,2,3)
                if extentType[ct] == 0:
                    extObj.data = True
                elif extentType[ct] == 2:
                    extObj.data = True
                elif extentType[ct] == 3:
                    extObj.data = False

                extObj.offset = start
                extObj.length = extentLength[ct]

                extentList.append(extObj)
                start+=extentLength[ct]
                ct+=1
            startCt=start

        return extentList
