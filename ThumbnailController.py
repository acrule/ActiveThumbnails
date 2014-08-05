from AppKit import *
from Cocoa import *
import Quartz.CoreGraphics as CG

import os
import time
import datetime
import string

import sqlalchemy
from sqlalchemy.orm import sessionmaker, mapper, join
from sqlalchemy.dialects.sqlite.base import dialect

import models
from models import Experience, Debrief, Cue

import mutagen.mp4


class ActiveThumbnailsController(NSWindowController):
    mainImage = objc.IBOutlet()
    nextButton = objc.IBOutlet()
    prevButton = objc.IBOutlet()

    slider = objc.IBOutlet()
    label = objc.IBOutlet()

    extentDropdown = objc.IBOutlet()
    sizeDropdown = objc.IBOutlet()

    cueTypeDropdown = objc.IBOutlet()
    animationTypeDropdown = objc.IBOutlet()
    animationSpeedDropdown = objc.IBOutlet()
    animationSpanDropdown = objc.IBOutlet()
    animationAdjacencyDropdown = objc.IBOutlet()
    animationButton = objc.IBOutlet()

    recordButton = objc.IBOutlet()
    existAudioText = objc.IBOutlet()
    playAudioButton = objc.IBOutlet()
    deleteAudioButton = objc.IBOutlet()

    recordingAudio = False
    playingAudio = False
    audio_file = ''

    animationView = objc.IBOutlet()
    experienceView = objc.IBOutlet()

    arrayController = objc.IBOutlet()

    # images for audio recording button
    recordImage = NSImage.alloc().initByReferencingFile_('../Resources/record.png')
    recordImage.setScalesWhenResized_(True)
    recordImage.setSize_((11, 11))

    stopImage = NSImage.alloc().initByReferencingFile_('../Resources/stop.png')
    stopImage.setScalesWhenResized_(True)
    stopImage.setSize_((11, 11))


    image = True
    snippet = True
    extent = 0

    screenH = NSScreen.mainScreen().frame().size.height
    screenW = NSScreen.mainScreen().frame().size.width
    screenR = screenW / (screenH * 1.0)
    h = 200
    w = 200 * screenR

    animationRelative = True
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

    def trycommit(self):
        self.last_commit = time.time()
        for _ in xrange(1000):
            try:
                self.session.commit()
                break
            except sqlalchemy.exc.OperationalError:
                print "Database operational error. Your storage device may be full."
                self.session.rollback()

                alert = NSAlert.alloc().init()
                alert.addButtonWithTitle_("OK")
                alert.setMessageText_("Database operational error. Your storage device may be full.")
                alert.setAlertStyle_(NSWarningAlertStyle)
                alert.runModal()

                break
            except:
                print "Rollback"
                self.session.rollback()


    @objc.IBAction
    def changeThumbnailType_(self, notification):
        if(notification.selectedItem().tag() == 1):
            self.animationView.setHidden_(False)
        else:
            self.animationView.setHidden_(True)


    @objc.IBAction
    def changeExtent_(self, notification):
        self.extent = notification.selectedItem().tag()
        self.loadImage_(self.files[self.index])


    @objc.IBAction
    def changeSize_(self, notification):
        self.h = self.activeController.sizeDropdown.selectedItem().tag()
        self.w = self.h * self.screenR

        self.loadImage_(self.files[self.index])


    @objc.IBAction
    def changeAnimationType_(self, notification):
        if(notification.selectedItem().tag() == 1):
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
            menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(str(s) + ' px ' , '', '')
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

        speeds = [1,2,5,10,15,30,60]
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
        models.Base.metadata.create_all(engine)

        # metadata = sqlalchemy.MetaData(engine)
        # experience = sqlalchemy.Table('experience', metadata, autoload=True)
        # mapper(Experience, experience)
        # debrief = sqlalchemy.Table('debrief', metadata, autoload=True)
        # mapper(Debrief, debrief)

        return sessionmaker(bind=engine)


    def populateExperienceTable(self, session):
        q = session.query(Debrief, Experience).join(Experience, Experience.id==Debrief.experience_id).all()
        # query to just get experience sample
        # q = session.query(Experience).all()
        for r in q:
            img = r.Experience.screenshot.split('/')[-1]
            dict = {}
            dict['time'] = img[2:4] + "/" + img[4:6] +"/"+ img[0:2] + " " +img[7:9] +":"+ img[9:11]
            dict['project'] = r.Experience.project
            dict['screenshot'] = r.Experience.screenshot
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

        recordToNative = experienceImage.size().height / self.screenH
        recordToDisplay = experienceImage.size().height / 600.0
        dispalyToNative = 600.0 / self.screenH

        x = float(path.split("_")[-2]) * recordToNative
        y = float(path.split("_")[-1].split('-')[0].split('.')[0]) * recordToNative

        targetImage = NSImage.alloc().initWithSize_(NSMakeSize(self.w, self.h))

        if(self.extent == 0):
            fromRect = CG.CGRectMake(0.0, 0.0, experienceImage.size().width, experienceImage.size().height)
            toRect = CG.CGRectMake(0.0, 0.0, self.w, self.h)
        elif(self.extent == 1):
            fromRect = CG.CGRectMake(x - self.w/2*recordToDisplay, y- self.h/2*recordToDisplay, self.w*recordToDisplay, self.h*recordToDisplay)
            toRect = CG.CGRectMake(0.0, 0.0, self.w, self.h)
        elif(self.extent == 2):
            targetImage = NSImage.alloc().initWithSize_(NSMakeSize(960.0, 600.0))
            fromRect = CG.CGRectMake(x - self.w/2*recordToDisplay, y - self.h/2*recordToDisplay, self.w*recordToDisplay, self.h*recordToDisplay)
            toRect = CG.CGRectMake(x/recordToDisplay - self.w/2, y/recordToDisplay- self.h/2, self.w, self.h)
        else:
            x = 1

        targetImage.lockFocus()
        experienceImage.drawInRect_fromRect_operation_fraction_( toRect, fromRect, NSCompositeCopy, 1.0 )
        targetImage.unlockFocus()

        self.mainImage.setImage_(targetImage)
        self.label.setStringValue_(img[2:4] + "/" + img[4:6] +"/"+ img[0:2] + " " +img[7:9] +":"+ img[9:11] +":"+ img[11:13])

        audioFiles = os.listdir(os.path.expanduser('~/.selfspy/audio'))
        audioName = self.files[self.index][:-4] + '-week.m4a'
        if (audioName in audioFiles):
            self.audio_file = audioName
            self.activeController.recordButton.setEnabled_(False)
            self.activeController.existAudioText.setStringValue_("You've recorded an answer:")
            self.activeController.playAudioButton.setHidden_(False)
            self.activeController.deleteAudioButton.setHidden_(False)
        else:
            self.activeController.recordButton.setEnabled_(True)
            self.activeController.existAudioText.setStringValue_("Record your answer here:")
            self.activeController.playAudioButton.setHidden_(True)
            self.activeController.deleteAudioButton.setHidden_(True)

        if self.index == 0:
            self.prevButton.setEnabled_(False)
        else:
            self.prevButton.setEnabled_(True)

        if self.index >= len(self.files)-1:
            self.nextButton.setEnabled_(False)
        else:
            self.nextButton.setEnabled_(True)

    @objc.IBAction
    def toggleAudioPlay_(self, sender):
        if self.playingAudio:
            self.playingAudio = False
            s = NSAppleScript.alloc().initWithSource_("tell application \"QuickTime Player\" \n stop the front document \n close the front document \n end tell")
            s.executeAndReturnError_(None)

            self.activeController.playAudioButton.setTitle_("Play Audio")

        else:
            self.playingAudio = True

            audio = mutagen.mp4.MP4(self.audio_file)
            length = audio.info.length

            s = NSAppleScript.alloc().initWithSource_("set filePath to POSIX file \"" + self.audio_file + "\" \n tell application \"QuickTime Player\" \n open filePath \n tell application \"System Events\" \n set visible of process \"QuickTime Player\" to false \n repeat until visible of process \"QuickTime Player\" is false \n end repeat \n end tell \n play the front document \n end tell")
            s.executeAndReturnError_(None)

            s = objc.selector(self.stopAudioPlay,signature='v@:')
            self.exp_time = NSUserDefaultsController.sharedUserDefaultsController().values().valueForKey_('experienceTime')
            self.experienceTimer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(length, self, s, None, False)

            self.activeController.playAudioButton.setTitle_("Stop Audio")

    def stopAudioPlay(self):
        self.playingAudio = False
        s = NSAppleScript.alloc().initWithSource_("tell application \"QuickTime Player\" \n stop the front document \n close the front document \n end tell")
        s.executeAndReturnError_(None)

        self.activeController.playAudioButton.setTitle_("Play Audio")

    @objc.IBAction
    def deleteAudio_(self, sender):
        controller = self.activeController

        if (self.audio_file != '') & (self.audio_file != None) :
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)
        self.audio_file = ''

        controller.recordButton.setEnabled_(True)
        controller.existAudioText.setStringValue_("Record your answer here:")
        controller.playAudioButton.setHidden_(True)
        controller.deleteAudioButton.setHidden_(True)

    @objc.IBAction
    def toggleAudioRecording_(self, sender):
        controller = self.activeController

        if self.recordingAudio:
            self.recordingAudio = False

            print "Stop Audio recording"
            # seems to miss reading the name sometimes
            imageName = str(self.files[self.index])[0:-4]

            if (imageName == None) | (imageName == ''):
                imageName = datetime.now().strftime("%y%m%d-%H%M%S%f") + '-audio'
            imageName = str(os.path.join(os.path.expanduser('~/.selfspy'), "audio/")) + imageName + '-week.m4a'
            self.audio_file = imageName
            imageName = string.replace(imageName, "/", ":")
            imageName = imageName[1:]

            s = NSAppleScript.alloc().initWithSource_("set filePath to \"" + imageName + "\" \n set placetosaveFile to a reference to file filePath \n tell application \"QuickTime Player\" \n set mydocument to document 1 \n tell document 1 \n stop \n end tell \n set newRecordingDoc to first document whose name = \"untitled\" \n export newRecordingDoc in placetosaveFile using settings preset \"Audio Only\" \n close newRecordingDoc without saving \n quit \n end tell")
            s.executeAndReturnError_(None)

            size = self.activeController.sizeDropdown.selectedItem().tag()
            extent = self.activeController.extentDropdown.titleOfSelectedItem()
            cue_type = self.activeController.cueTypeDropdown.titleOfSelectedItem()
            span = self.activeController.animationSpanDropdown.selectedItem().tag()
            adjacency = self.activeController.animationAdjacencyDropdown.titleOfSelectedItem()
            animation_type = self.activeController.animationTypeDropdown.titleOfSelectedItem()
            speed = self.activeController.animationSpeedDropdown.selectedItem().tag()

            self.session.add(Cue(size, extent, cue_type, span, adjacency, animation_type, speed, self.audio_file))
            self.trycommit()

            controller.recordButton.setImage_(self.recordImage)

            controller.recordButton.setEnabled_(False)
            controller.existAudioText.setStringValue_("You've recorded an answer:")
            controller.playAudioButton.setHidden_(False)
            controller.deleteAudioButton.setHidden_(False)

        else:
            self.recordingAudio = True

            print "Start Audio Recording"
            s = NSAppleScript.alloc().initWithSource_("tell application \"QuickTime Player\" \n set new_recording to (new audio recording) \n tell new_recording \n start \n end tell \n tell application \"System Events\" \n set visible of process \"QuickTime Player\" to false \n repeat until visible of process \"QuickTime Player\" is false \n end repeat \n end tell \n end tell")
            s.executeAndReturnError_(None)

            self.activeController.recordButton.setImage_(self.stopImage)


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
        self.session_maker = self.createSession(self)
        self.session = self.session_maker()
        self.populateExperienceTable(self, self.session)

        desc = NSSortDescriptor.alloc().initWithKey_ascending_('time',False)
        descriptiorArray = [desc]
        self.activeController.arrayController.setSortDescriptors_(descriptiorArray)
        self.activeController.arrayController.rearrangeObjects()


    show = classmethod(show)
