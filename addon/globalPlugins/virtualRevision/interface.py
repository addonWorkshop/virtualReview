import addonHandler
import gui
import speech
import ui
import wx
from cursorManager import FindDialog

addonHandler.initTranslation()


class VirtualRevisionMainDialog(wx.Dialog):
    _last_find_text = None
    _last_find_text_case_sensitive = None

    def __init__(self, title: str, text: str):
        super().__init__(parent=gui.mainFrame, title=title, style=wx.CLOSE_BOX)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.output_field = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        self.main_sizer.Add(self.output_field, proportion=1, flag=wx.EXPAND)
        self.output_field.Bind(wx.EVT_KEY_DOWN, self.on_output_key_down)
        self.output_field.SetValue(text)
        self.SetEscapeId(wx.ID_CLOSE)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetSizer(self.main_sizer)
        self.main_sizer.Fit(self)

    @classmethod
    def show_main_dialog(cls, title: str, text: str):
        lines = [line.rstrip() for line in text.replace("\r", "").split("\n")]
        dialog = cls(title=title, text="\r\n".join(lines))
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
        if evt.ControlDown() and key == ord("F"):
            self.show_find_dialog()
            return
        if key == wx.WXK_F3:
            self.find(direction=-1 if evt.ShiftDown() else 1)
            return
        evt.Skip()

    def show_find_dialog(self, direction: int = 1):
        def run():
            gui.mainFrame.prePopup()
            dialog = FindDialog(
                gui.mainFrame,
                self,
                self._last_find_text or "",
                self._last_find_text_case_sensitive or False,
                direction == -1,
            )
            dialog.ShowModal()
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

    # Called by NVDA's FindDialog, hence the camelCase signature.
    def doFindText(self, text, reverse, caseSensitive):
        VirtualRevisionMainDialog._last_find_text = text
        VirtualRevisionMainDialog._last_find_text_case_sensitive = caseSensitive
        # wx positions count UTF-16 code units, so a surrogate pair takes two positions
        # while Python strings count it as one character.
        position = self.output_field.GetInsertionPoint()
        output = self.output_field.GetValue()
        correct_position = len(output.encode("utf-16-le")[: position * 2].decode("utf-16-le"))
        correct_position += -1 if reverse else 1
        if not caseSensitive:
            output = output.lower()
            text = text.lower()
        start, end = (0, correct_position) if reverse else (correct_position, len(output))
        index = (output.rfind if reverse else output.find)(text, start, end)
        if index > -1:
            # Translators: Reported when the searched text is found in the virtual review window.
            message = _("Found")
            self.output_field.SetInsertionPoint(len(output[:index].encode("utf-16-le")) // 2)
        else:
            # Translators: Reported when the searched text is not found in the virtual review window.
            message = _("Not found")
        speech.cancelSpeech()
        ui.message(message)
