from Foundation import NSObject
from Foundation import NSLog

import ThumbnailController


class ApplicationDelegate(NSObject):

    def init(self):
        self = super(ApplicationDelegate, self).init()
        return self


    def applicationDidFinishLaunching_(self, _):
        NSLog("applicationDidFinishLaunching_")
        ThumbnailController.ActiveThumbnailsController.show()


    def applicationWillTerminate_(self, sender):
        pass
