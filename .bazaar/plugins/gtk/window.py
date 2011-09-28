
import pygtk
import gtk

class Window(gtk.Window):

    def __init__(self, parent=None):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self._parent = parent

        self.connect('key-press-event', self._on_key_press)

    def _on_key_press(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if event.state & gtk.gdk.CONTROL_MASK:
            if keyname is "w":
                self.destroy()
                if self._parent is None:
                    gtk.main_quit()
            elif keyname is "q":
                gtk.main_quit()

