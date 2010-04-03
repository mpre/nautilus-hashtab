import os
import re
import hashlib
import urllib
import gtk
import nautilus
import binascii

class HashTab(nautilus.PropertyPageProvider):
    
    def __init__(self):
        pass

    def get_property_pages(self, files):
        if len(files) != 1:
            return
        
        obj = files[0]
        
        if obj.get_uri_scheme() != 'file':
            return
        
        if obj.is_directory():
            return

        file_path = obj.get_uri()[7:].replace("%20"," ")

        # Tab Label
        tab_label = gtk.Label('HashTab')
        tab_label.show()

        self.HASH_TYPES = ('SHA1', 'SHA256', 'SHA512', 'MD5', 'CRC32')

        # Settings dict
        self.type_conf = self.load_conf()

        main_frame = gtk.VBox(False, 10)
        main_align = gtk.Alignment(0.85,0.85,0.99,0.85) # I don't know why but it works
        self.hash_tree_view = gtk.TreeView(gtk.ListStore(str,str))
        
        hash_scrolled_win = gtk.ScrolledWindow()
        
        self.hash_entry = gtk.Entry()
        entry_label = gtk.Label("Enter your hash here:")
        entry_frame = gtk.HBox(False, 10)
       
        compare_button = gtk.Button('Check')
        start_hash_button = gtk.Button("Hash It!")
        settings_button = gtk.Button("Settings")
        buttonbox = gtk.HButtonBox()
        buttonbox_align = gtk.Alignment(1,1,0,0)
        self.event_box = gtk.EventBox()
        self.result_label = gtk.Label()
        bottom_box = gtk.HBox(False,10)
 
        self.hash_tree_view.append_column(self.create_col('Type', 0))
        self.hash_tree_view.append_column(self.create_col('Value', 1))

        self.hash_tree_view.connect("button_press_event", self.pop_up)

        hash_scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        hash_scrolled_win.set_size_request(10,240)

        self.hash_entry.connect("activate", self.check_hash)
        entry_label.set_size_request(1,-1)
        
        start_hash_button.connect("clicked", self.calc_hash, file_path)
        compare_button.connect("clicked", self.check_hash)
        settings_button.connect("clicked", self.show_settings)
 
        #Time to pack
        hash_scrolled_win.add_with_viewport(self.hash_tree_view)
        buttonbox.pack_start(compare_button)
        buttonbox.pack_start(start_hash_button)
        buttonbox.pack_end(settings_button)
        buttonbox_align.add(buttonbox)
        self.event_box.add(self.result_label)
        bottom_box.pack_start(self.event_box)
        bottom_box.pack_start(buttonbox_align)
        entry_frame.pack_start(entry_label)
        entry_frame.pack_start(self.hash_entry)
        main_frame.pack_start(hash_scrolled_win)
        main_frame.pack_start(entry_frame)
        main_frame.pack_start(bottom_box)

        main_align.add(main_frame)
        main_align.show_all()

        return nautilus.PropertyPage("NautilusPython::HashTab", tab_label, main_align),

    def load_conf(self):
        configuration = {}
        conf_file_path = os.path.expanduser("~") +  '/.hash_tab_conf'
        if not os.path.isfile(conf_file_path):
            self.make_configuration_file(conf_file_path)
        for line in open(conf_file_path, 'r'):
            line = re.sub('\s+','',line) #delete whitespace
            if not line.startswith('#') and line.find('=') != -1:
                hash_type = line[:line.index('=')]
                if line.find('#') != -1:  # single line comment
                    end = line.index('#')
                else:
                    end = len(line)
                hash_enabled = line[line.index('=') + 1:end]
                configuration[hash_type] = hash_enabled
        return configuration
    
    def make_configuration_file(self, file_path):
        # The configuration file doesn't exist, let's create a standard settings
        # All Hash are disabled by default, let's put some comment too
        try: 
            conf_file = open(file_path, 'w')
            conf_file.write('# This is the configuration file for nautilus HashTab extension \n')
            conf_file.write('# Line that begins with "#" are comment \n')
            conf_file.write('# Type equal to False are disabled, type equal to True are enabled, don\'t enable many hash type or hashing will require much time \n \n')
            for hash_type in self.HASH_TYPES:
                conf_file.write('{0}=False\n'.format(hash_type))            
            conf_file.close()
        except error:
            pass
        return

    def create_col(self, col_name, index):
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(col_name, cell, text = index)
        return column

    def calc_hash(self, widget, file_path):
        selection = self.hash_tree_view.get_selection()
        model, it = selection.get_selected()
        model.clear()
        for hash_type in self.type_conf.keys():
            if self.type_conf[hash_type] == '1' or self.type_conf[hash_type] == 'True':# If it's True we should calc this hash
                f = open(file_path, 'rb')
                if hash_type.lower() in ('md5', 'sha1', 'sha512', 'sha224', 'sha256', 'sha384'): # hashlib function
                    function = "hashlib.{0}()".format(hash_type.lower())
                    m = eval(function)
                    data = f.read(10240)
                    while (len(data) != 0):
                        m.update(data)
                        data = f.read(10240)
                    hash_value = str(m.hexdigest())
                elif hash_type.lower() in ('crc32'):
                    m = binascii.crc32("") & 0xffffffff
                    data = f.read(10240)
                    while (len(data) != 0):
                        m = binascii.crc32(data, m) & 0xffffffff
                        data = f.read(10240)
                    hash_value = str(hex(m))[2:]
                selection = self.hash_tree_view.get_selection()
                model, it = selection.get_selected()
                model.append([hash_type, hash_value])
                f.close()
        self.hash_tree_view.set_cursor(0)
        return

    def check_hash(self, widget):
        given_hash = self.hash_entry.get_text()
        selection = self.hash_tree_view.get_selection()
        model, it = selection.get_selected()
        if it:
            if given_hash == model.get_value(it, 1):
                self.event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("light green"))
                self.result_label.set_label("Correct hash")
            else:
                self.event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("indian red"))
                self.result_label.set_label("Wrong hash")
        else:
            self.event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("light yellow"))
            self.result_label.set_label('Select an hash from the table \n or click the "Hash it!" button')
        return

    def show_settings(self, widget):
        # Show the settings window
        check_list = {}
        self.settings_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        check_box = gtk.VBox(False, 5)
        box = gtk.VBox(False, 5)
        check_box_align = gtk.Alignment(0,0,0,0)
        buttonbox = gtk.HButtonBox()
        quit_b = gtk.Button(stock=gtk.STOCK_QUIT)
        apply_b = gtk.Button(stock=gtk.STOCK_APPLY)
        buttonbox_align = gtk.Alignment(1,1,0,0)

        self.settings_win.set_size_request(200, -1)
        self.settings_win.set_title('HashTab settings')
        self.settings_win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.settings_win.set_keep_above(True)

        quit_b.connect("clicked", self.close_set_win)
        apply_b.connect("clicked", self.apply_conf, check_list)

        buttonbox.pack_start(apply_b)        
        buttonbox.pack_start(quit_b)
        buttonbox_align.add(buttonbox)

        for h_t in self.type_conf.keys():
            check_list[h_t] = gtk.CheckButton(str(h_t))
            if self.type_conf[h_t] == '1' or self.type_conf[h_t] == 'True':
                check_list[h_t].set_active(True)
            check_box.pack_start(check_list[h_t])
        check_box_align.add(check_box)
        box.pack_start(check_box_align)
        box.pack_end(buttonbox_align)
        self.settings_win.add(box)
        self.settings_win.show_all()
       
        return

    def close_set_win(self, widget):
        self.settings_win.destroy()

    def apply_conf(self, widget, check_list):
        conf_file_path = os.path.expanduser("~") +  '/.hash_tab_conf'
        content_to_write = ""
        for line in open(conf_file_path, 'r'):
            if line.startswith('#') or line.find('=') == -1:
                content_to_write += line
            else:
                # Set configration according to check_list
                hash_type = line[:line.index('=')]
                content_to_write += hash_type
                content_to_write += str("=")
                content_to_write += str(check_list.get(hash_type, gtk.CheckButton).get_active())
                content_to_write += "\n"
        f = open(conf_file_path, 'w')
        for line in content_to_write:
            f.write(line)
        f.close()

        # Reload configuration
        self.type_conf = self.load_conf()
        self.settings_win.destroy()

        return

    def pop_up(self, widget, event):
        if event.button == 3:
            copy_menu = gtk.Menu()
            item_copy_hash = gtk.MenuItem(label = "Copy hash to clipboard")
            item_copy_row = gtk.MenuItem(label = "Copy row to clipboard")

            item_copy_hash.connect("activate", self.copy_hash_to_clipboard)
            item_copy_row.connect("activate", self.copy_row_to_clipboard)

            copy_menu.append(item_copy_hash)
            copy_menu.append(item_copy_row)

            copy_menu.show_all()
            copy_menu.popup(None, None, None, event.button, event.time)

    def copy_hash_to_clipboard(self, widget):
        selection = self.hash_tree_view.get_selection()
        model, it = selection.get_selected()
        if it:
            selected_hash = model.get_value(it, 1)
            clipboard = gtk.Clipboard(gtk.gdk.display_manager_get().get_default_display(), "CLIPBOARD")
            clipboard.set_text(selected_hash)
  
    def copy_row_to_clipboard(self, widget):
        selection = self.hash_tree_view.get_selection()
        model, it = selection.get_selected()
        if it:
            selected_hash = "{0} : {1}".format(model.get_value(it, 0), model.get_value(it, 1))
            clipboard = gtk.Clipboard(gtk.gdk.display_manager_get().get_default_display(), "CLIPBOARD")
            clipboard.set_text(selected_hash)
