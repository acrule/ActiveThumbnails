from AppKit import *
from Cocoa import *
import Quartz.CoreGraphics as CG

import os
import datetime
import sqlalchemy
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.dialects.sqlite.base import dialect


class Experience(object):
    pass


class ActiveThumbnailsController(NSWindowController):
    mainImage = objc.IBOutlet()
    nextButton = objc.IBOutlet()
    prevButton = objc.IBOutlet()

    slider = objc.IBOutlet()
    label = objc.IBOutlet()

    extentButton = objc.IBOutlet()
    sizeDropdown = objc.IBOutlet()

    animationTypeButton = objc.IBOutlet()
    animationSpeedDropdown = objc.IBOutlet()
    animationSpanDropdown = objc.IBOutlet()
    animationAdjacencyDropdown = objc.IBOutlet()
    animationButton = objc.IBOutlet()

    animationView = objc.IBOutlet()
    experienceView = objc.IBOutlet()

    arrayController = objc.IBOutlet()


    image = True
    snippet = True

    screenH = NSScreen.mainScreen().frame().size.height
    screenW = NSScreen.mainScreen().frame().size.width
    screenR = screenW / (screenH * 1.0)
    h = 200
    w = 200 * screenR

    animationRelative = False
    animationSpan = 60
    animationAdjacency = -1
    animationSpeed = 5

    index = 0
    animationIndex = 0

    list = []

    results = [ NSDictionary.dictionaryWithDictionary_(x) for x in list]

    def windowDidLoad(self):
        NSWindowController.windowDidLoad(self)

        self.files = os.listdir(os.path.expanduser("~/.selfspy/screenshots"))
        self.index = len(self.files)-1
        self.loadImage_(self.files[self.index])

        self.slider.setMaxValue_(len(self.files)-1)
        self.slider.setIntValue_(len(self.files)-1)

        NSLog("Active Thumbnails has finished loading.")


    @objc.IBAction
    def changeThumbnailType_(self, notification):
        if(notification.selectedSegment() == 1):
            self.animationView.setHidden_(False)
        else:
            self.animationView.setHidden_(True)


    @objc.IBAction
    def changeExtent_(self, notification):
        if(notification.selectedSegment() == 1):
            self.snippet = True
        else:
            self.snippet = False
        self.loadImage_(self.files[self.index])


    @objc.IBAction
    def changeSize_(self, notification):
        self.h = self.activeController.sizeDropdown.selectedItem().tag()
        self.w = self.h * self.screenR

        self.loadImage_(self.files[self.index])


    @objc.IBAction
    def changeAnimationType_(self, notification):
        if(notification.selectedSegment() == 1):
            self.animationRelative = False
        else:
            self.animationRelative = True
        self.populateSpeedDropdown()


    @objc.IBAction
    def changeSpeed_(self, notification):
        self.animationSpeed = self.activeController.animationSpeedDropdown.selectedItem().tag()


    @objc.IBAction
    def changeSpan_(self, notification):
        self.animationSpan = self.activeController.animationSpanDropdown.selectedItem().tag()


    @objc.IBAction
    def changeAdjacency_(self, notification):
        self.animationAdjacency = self.activeController.animationAdjacencyDropdown.selectedItem().tag()


    @objc.IBAction
    def nextImage_(self,sender):
        self.index += 1
        self.slider.setIntValue_(self.index)
        self.loadImage_(self.files[self.index])


    @objc.IBAction
    def prevImage_(self,sender):
        self.index -= 1
        self.slider.setIntValue_(self.index)
        self.loadImage_(self.files[self.index])

    @objc.IBAction
    def slide_(self, sender):
        self.index = self.slider.intValue()
        self.loadImage_(self.files[self.index])


    def populateSizeDropdown(self):
        sizes = []
        for s in range(30):
            sizes.append((s + 1) * 20)

        for s in sizes:
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(str(s) + ' x ' +str(int(s * self.screenR)) , '', '')
            menuitem.setTag_(s)
            self.activeController.sizeDropdown.menu().addItem_(menuitem)
        try:
            self.activeController.sizeDropdown.selectItemWithTag_(200)
        except:
            print("Could not select default size dropdown item")


    def populateSpeedDropdown(self):
        tag = ""
        if self.animationRelative:
            tag = "x"
        else:
            tag = "fps"

        self.activeController.animationSpeedDropdown.menu().removeAllItems()

        speeds = [1,2,5,10,15,30]
        for s in speeds:
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(str(s) + tag , '', '')
            menuitem.setTag_(s)
            self.activeController.animationSpeedDropdown.menu().addItem_(menuitem)
        try:
            self.activeController.animationSpeedDropdown.selectItemWithTag_(5)
        except:
            print("Could not select default size dropdown item")


    def createSession(self):
        dbPath = os.path.expanduser('~/.selfspy/selfspy.sqlite')
        engine = sqlalchemy.create_engine('sqlite:///%s' % dbPath)

        metadata = sqlalchemy.MetaData(engine)
        experience = sqlalchemy.Table('experience', metadata, autoload=True)
        mapper(Experience, experience)

        Session = sessionmaker(bind=engine)
        session = Session()
        q = session.query(Experience).all()
        return session


    def populateExperienceTable(self, session):
        q = session.query(Experience).all()
        for r in q:
            img = r.screenshot.split('/')[-1]
            dict = {}
            dict['time'] = img[2:4] + "/" + img[4:6] +"/"+ img[0:2] + " " +img[7:9] +":"+ img[9:11]
            dict['project'] = r.project
            dict['screenshot'] = r.screenshot
            self.results.append(NSDictionary.dictionaryWithDictionary_(dict))

    def goToExperience_(self,sender):
        selectedObjs = self.arrayController.selectedObjects()
        if len(selectedObjs) == 0:
            NSLog(u"No selected row!")
            return

        row = selectedObjs[0]
        if not row.has_key('screenshot') or row['screenshot'] == None:
            NSLog(u"Row has no screenshot!")
            return

        self.index = self.files.index(row['screenshot'].split('/')[-1])

        self.loadImage_(self.files[self.index])
        self.slider.setIntValue_(self.index)


    def runAnimation(self):
        self.animationIndex += 1
        self.loadImage_(self.frames[self.animationIndex])

        if (self.animationIndex >= len(self.frames)-1):
            s = objc.selector(self.showCurrent,signature='v@:')
            self.animationTimer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.5, self, s, None, False)
        else:
            if self.animationRelative:
                delay = self.timings[self.animationIndex] / self.animationSpeed
            else:
                delay = 1.0 / self.animationSpeed

            s = objc.selector(self.runAnimation,signature='v@:')
            self.animationTimer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(delay, self, s, None, False)


    def showCurrent(self):
        self.loadImage_(self.files[self.index])
        self.animationButton.setEnabled_(True)


    @objc.IBAction
    def getAnimationFrames_(self, notification):
        self.animationButton.setEnabled_(False)
        self.frames = filter(self.checkTime_ , self.files)

        self.timings = []
        for f in self.frames:
            self.timings.append(datetime.datetime.strptime(f.split('_')[0], "%y%m%d-%H%M%S%f"))
        for t in range(len(self.timings)-1):
            self.timings[t] = (self.timings[t+1] - self.timings[t]).total_seconds()

        if len(self.frames) >=2:
            self.timings[-1] = 0
            self.animationIndex = 0
            self.loadImage_(self.frames[self.animationIndex])

            if self.animationRelative:
                delay = self.timings[self.animationIndex] / self.animationSpeed
            else:
                delay = 1.0 / self.animationSpeed

            s = objc.selector(self.runAnimation,signature='v@:')
            self.animationTimer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(delay, self, s, None, False)
        else:
            NSLog("Cannot run animaiton with less than 2 images")
            self.animationButton.setEnabled_(True)


    def checkTime_(self, x):
        span = datetime.timedelta(seconds = self.animationSpan)
        now = datetime.datetime.strptime(self.files[self.index].split('_')[0], "%y%m%d-%H%M%S%f")

        if(self.animationAdjacency == -1):
            start = now - span
            end = now
        elif(self.animationAdjacency == 0):
            start = now - span/2
            end = now + span/2
        else:
            start = now
            end = now + span

        start = datetime.datetime.strftime(start, "%y%m%d-%H%M%S%f")
        end = datetime.datetime.strftime(end, "%y%m%d-%H%M%S%f")

        return ((x >= start) & (x <= end))

    def loadImage_(self, img):
        path = os.path.join("~/.selfspy/screenshots/", img)
        path = os.path.expanduser(path)
        experienceImage = NSImage.alloc().initByReferencingFile_(path)

        scaleFactor = experienceImage.size().height / self.screenH

        x = float(path.split("_")[-2]) * scaleFactor
        y = float(path.split("_")[-1].split('-')[0].split('.')[0]) * scaleFactor

        targetImage = NSImage.alloc().initWithSize_(NSMakeSize(self.w, self.h))

        if(self.snippet):
            fromRect = CG.CGRectMake(x - self.w/2, y- self.h/2, self.w, self.h)
        else:
            fromRect = CG.CGRectMake(0.0, 0.0, experienceImage.size().width, experienceImage.size().height)

        toRect = CG.CGRectMake(0.0, 0.0, self.w, self.h)

        targetImage.lockFocus()
        experienceImage.drawInRect_fromRect_operation_fraction_( toRect, fromRect, NSCompositeCopy, 1.0 )
        targetImage.unlockFocus()

        self.mainImage.setImage_(targetImage)
        self.label.setStringValue_(img[2:4] + "/" + img[4:6] +"/"+ img[0:2] + " " +img[7:9] +":"+ img[9:11] +"."+ img[11:13])

        if self.index == 0:
            self.prevButton.setEnabled_(False)
        else:
            self.prevButton.setEnabled_(True)

        if self.index >= len(self.files)-1:
            self.nextButton.setEnabled_(False)
        else:
            self.nextButton.setEnabled_(True)


    def awakeFromNib(self):
        if self.experienceView:
            self.experienceView.setTarget_(self)
            self.experienceView.setDoubleAction_("goToExperience:")


    def show(self):
        try:
            if self.activeController:
                self.activeController.close()
        except:
            pass

        # open window from NIB file, show front and center
        self.activeController = ActiveThumbnailsController.alloc().initWithWindowNibName_("ActiveThumbnails")
        self.activeController.showWindow_(None)
        self.activeController.window().makeKeyAndOrderFront_(None)
        self.activeController.window().center()
        self.activeController.retain()

        self.populateSizeDropdown(self)
        self.populateSpeedDropdown(self)
        self.session = self.createSession(self)
        self.populateExperienceTable(self, self.session)
        self.activeController.arrayController.rearrangeObjects()


    show = classmethod(show)
