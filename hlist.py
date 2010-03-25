import os
import re
import hashlib
import urllib
import gtk
import nautilus

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

        self.HASH_TYPES = ('MD5', 'SHA1', 'SHA512')

        # Settings dict
        type_conf = self.load_conf()

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

        hash_scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        hash_scrolled_win.set_size_request(10,240)

        entry_label.set_size_request(1,-1)
        
        start_hash_button.connect("clicked", self.calc_hash, type_conf, file_path)
        compare_button.connect("clicked", self.check_hash)
 
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
            conf_file.write('# Type equal to 0 are disabled, type equal to 1 are enabled, don\'t enable many hash type or hashing will require much time \n \n')
            for hash_type in self.HASH_TYPES:
                conf_file.write('{0}=0\n'.format(hash_type))            
            conf_file.close()
        except error:
            pass
        return

    def create_col(self, col_name, index):
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(col_name, cell, text = index)
        return column

    def calc_hash(self, widget, type_conf, file_path):
        selection = self.hash_tree_view.get_selection()
        model, it = selection.get_selected()
        model.clear()
        for hash_type in type_conf.keys():
            if type_conf[hash_type] == '1': # If it's True we should calc this hash
                if hash_type.lower() in ('md5', 'sha1', 'sha512', 'sha224', 'sha256', 'sha384'): # hashlib function
                    f = open(file_path, 'rb')
                    function = "hashlib.{0}()".format(hash_type.lower())
                    m = eval(function)
                    data = f.read(10240)
                    while (len(data) != 0):
                        m.update(data)
                        data = f.read(10240)
                    f.close()
                    selection = self.hash_tree_view.get_selection()
                    model, it = selection.get_selected()
                    model.append([hash_type, m.hexdigest()])
        self.hash_tree_view.set_cursor(0)
        return

    def check_hash(self, widget):
        given_hash = self.hash_entry.get_text()
        selection = self.hash_tree_view.get_selection()
        model, it = selection.get_selected()
        if it:
            if given_hash == model.get_value(it, 1):
                self.event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("green"))
                self.result_label.set_label("Ok")
            else:
                self.event_box.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
                self.result_label.set_label("Ko")
        else:
            self.result_label.set_label("Select an hash from the table")
        return
