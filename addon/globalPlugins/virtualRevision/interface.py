import addonHandler
import config
import gui
import ui
import speech
import wx
from gui.guiHelper import BoxSizerHelper
from cursorManager import FindDialog
addonHandler.initTranslation()


class VirtualRevisionSettingsPanel(gui.settingsDialogs.SettingsPanel):
    title = addonHandler.getCodeAddon().manifest['summary']

    def makeSettings(self, settings_sizer):
        self.config = config.conf[addonHandler.getCodeAddon().name]
        sizer = gui.guiHelper.BoxSizerHelper(self, sizer=settings_sizer)
        self.UIAConsoleGrabbingCB = sizer.addItem(wx.CheckBox(
            self,
            label=_('Always use UIA implementation for consoles (gets more text)'),
        ))
        self.UIAConsoleGrabbingCB.SetValue(self.config['UIAConsoleGrabbing'])

    def onSave(self):
        self.config['UIAConsoleGrabbing'] = self.UIAConsoleGrabbingCB.IsChecked()

    @classmethod
    def addSettingsPanel(cls):
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(VirtualRevisionSettingsPanel)

    @classmethod
    def removeSettingsPanel(cls):
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(cls)


class VirtualRevisionMainDialog(wx.Dialog):
    _last_find_text = None
    _last_find_text_case_sensitive = None

    def __init__(self, title: str, text: str):
        super().__init__(parent=gui.mainFrame, title=title, style=wx.CLOSE_BOX)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.output_field = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH)
        self.main_sizer.Add(self.output_field,             proportion=1, flag=wx.EXPAND)
        self.output_field.Bind(wx.EVT_KEY_DOWN, self.on_output_key_down)
        self.output_field.write(text)
        self.SetEscapeId(wx.ID_CLOSE)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetSizer(self.main_sizer)
        self.main_sizer.Fit(self)

    @classmethod
    def show_main_dialog(cls, title: str, text: str):
        dialog = cls(title=title, text=text)
        gui.mainFrame.Raise()
        dialog.Show()
        dialog.Maximize()
        dialog.SetFocus()

    def on_close(self, event):
        self.Destroy()

    def on_output_key_down(self, evt):
        key = evt.GetKeyCode()
        if key == wx.WXK_ESCAPE:
            self.Close()
            return
        if evt.ControlDown() and key == ord('F'):
            self.show_find_dialog()
            return
        if key == wx.WXK_F3:
            self.find(direction=-1) if evt.ShiftDown() else self.find(direction=1)
            return
        evt.Skip()

    def show_find_dialog(self, direction: int = 1):
        def run():
            gui.mainFrame.prePopup()
            d = FindDialog(gui.mainFrame, self, self._last_find_text or '', self._last_find_text_case_sensitive or False, direction == -1)
            d.ShowModal()
            gui.mainFrame.postPopup()
        wx.CallAfter(run)

    def find(self, direction: int):
        last_text = VirtualRevisionMainDialog._last_find_text 
        if last_text is None:
            self.show_find_dialog(direction=direction)
            return
        self.doFindText(
            last_text,
            reverse=direction == -1,
            caseSensitive=VirtualRevisionMainDialog._last_find_text_case_sensitive,
        )

    def doFindText(self, text, reverse, caseSensitive):
        VirtualRevisionMainDialog._last_find_text = text
        VirtualRevisionMainDialog._last_find_text_case_sensitive = caseSensitive
        position = self.output_field.GetInsertionPoint()+1
        output = self.output_field.GetValue()
        if not caseSensitive:
            output = output.lower()
            text = text.lower()
        start, end = (0, position) if reverse else (position, len(output))
        index = (output.rfind if reverse else output.find)(text, start, end)
        if index > -1:
            message = 'Found'
            self.output_field.SetInsertionPoint(index)
        else:
            message = 'Not found'
        speech.cancelSpeech()
        ui.message(message)
