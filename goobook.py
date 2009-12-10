#!/usr/bin/env python
import sys
import os
import re
import pickle
from datetime import datetime

from gdata.contacts.service import ContactsService, ContactsQuery
from gdata.contacts import ContactEntry, Email
import atom

class GooBook(object):
    def __init__ (self, username, password, max_results, cache_filename):
        self.username = username
        self.password = password
        self.max_results = max_results
        self.cache_filename = cache_filename
        self.addrbk = {}

    def query(self, query):
        """
        Do the query, and print it out in
        """
        self.load()
        match = re.compile(query, re.I).search
        resultados = dict([(k,v) for k,v in self.addrbk.items() if match(k) or match(v)])
        print "\n"
        for (k,v) in resultados.items():
            print "%s\t%s"%(k,v)

    def load(self):
        """
        Load the cached addressbook feed, or fetch it (again) if it is
        old or missing or invalid or anyting
        """
        try:
            picklefile = file(self.cache_filename, 'rb')
        except IOError:
            # we should probably catch picke errors too...
            self.fetch()
            #  simplifico el feed, con formato 'titulo'\t'email' sin ''
        else:
            stamp, self.addrbk = pickle.load(picklefile) #optimizar
            if (datetime.now() - stamp).days:
                self.fetch()
        finally:
            self.store()


    def fetch(self):
        """
        Actually go out on the wire and fetch the addressbook.

        """
        client = ContactsService()
        client.ClientLogin(self.username, self.password)
        query = ContactsQuery()
        query.max_results = self.max_results
        feed = client.GetContactsFeed(query.ToUri())
        for e in feed.entry:
            for i in e.email:
                if e.title.text:
                    self.addrbk[i.address] = e.title.text
                else:
                    self.addrbk[i.address] = i.address

    def store(self):
        """
        Pickle the addressbook and a timestamp
        """
        picklefile = file(self.cache_filename, 'wb')
        stamp = datetime.now()
        pickle.dump((stamp, self.addrbk), picklefile)

    def add(self):
        """
        Add an address from From: field of a mail. This assumes a single mail file is supplied through stdin. . 
        """

        fromLine = ""
        for l in sys.stdin:
            if l.startswith("From: "): 
                fromLine = l
                break
        if fromLine == "":
            print "Not a valid mail file!"
            sys.exit(2) 
        #In a line like
        #From: John Doe <john@doe.com> 
        els = fromLine.split()
        #Drop "From: "
        del els[0]
        #get the last element as mail
        mailaddr = els[-1]
        if mailaddr.startswith("<"):
            mailaddr = mailaddr[1:]
        if mailaddr.endswith(">"):
            mailaddr = mailaddr[:-1]
        #and the rest as name
        name = " ".join(els[:-1])
        #save to contacts
        client = ContactsService()
        client.ClientLogin(self.username, self.password)
        new_contact = ContactEntry(title=atom.Title(text=name))
        new_contact.email.append(Email(address=mailaddr, primary='true'))
        contact_entry = client.CreateContact(new_contact)
        print contact_entry
        

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: python goobook.py query <name> or python goobook.py add <mail.at.stdin>>"
        sys.exit(1)

    try:
        from settings import USERNAME, PASSWORD, MAX_RESULTS, CACHE_FILENAME
    except ImportError:
        raise RuntimeError("Please create a valid settings.py"
                           " (look at settings_example.py for inspiration)")
    else:
        CACHE_FILENAME = os.path.realpath(os.path.expanduser(CACHE_FILENAME))

    goobk = GooBook(USERNAME, PASSWORD, MAX_RESULTS, CACHE_FILENAME)
    if sys.argv[1] == "query":
        if len(sys.argv) < 3:
            print "Usage: python goobook.py query <name> or python goobook.py add <mail.at.stdin>>"
            sys.exit(1)
        goobk.query(sys.argv[2])
    elif sys.argv[1] == "add":
        goobk.add()
    else:
            print "Usage: python goobook.py query <name> or python goobook.py add <mail.at.stdin>>"
        sys.exit(1)
        
