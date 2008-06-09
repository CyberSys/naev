#!/usr/bin/env python
"""
See Licensing and Copyright notice in resedit.py
"""

from xml.dom import minidom
import sets

def uniq(alist):    # Fastest order preserving
   s = sets.Set(alist)
   del alist[:]
   for a in s:
      alist.append(a)


def load(xmlfile, tag, has_name=True, do_array=None, do_special=None, do_special2=None):
   dom = minidom.parse(xmlfile)
   xmlNodes = dom.getElementsByTagName(tag)

   dictionary = {}
   for xmlNode in xmlNodes:

      mdic = {}
      # name is stored as a property and not a node
      if (has_name):
         name = xmlNode.attributes["name"].value

      # append the element to the dictionary
      for bignode in filter(lambda x: x.nodeType==x.ELEMENT_NODE, xmlNode.childNodes):
         mdic[bignode.nodeName], size = load_Tag( bignode, do_array, do_special, do_special2 )

      dictionary[name] = mdic
   
   dom.unlink()
   return dictionary


def load_Tag( node, do_array=None, do_special=None, do_special2=None ):

   i = 0

   # figure out if we need an array or dic
   array = []
   section = {}
   if (do_array != None and node.nodeName in do_array) or ( do_special != None and node.nodeName in do_special):
      use_array = True
   else:
      use_array = False

   for child in filter(lambda x: x.nodeType==x.ELEMENT_NODE, node.childNodes):
      n = 0
      children, n = load_Tag( child, do_array, do_special, do_special2 )

      # just slap the children on
      if n > 0:
         section[child.nodeName] = children
      
      # big ugly hack to use list instead of array
      #
      # -- PARAMETER FORMAT --
      # [KEY, ...]
      #
      # -- XML INPUT --
      # <KEY>
      #   <foo>xxx</foo>
      #   <foo>yyy</foo>
      #   ...
      # </KEY>
      #
      # -- PYTHON OUTPUT --
      # key:["xxx","xxx",...]
      #
      elif use_array and node.nodeName in do_array:
         array.append(child.firstChild.data)

      # uglier hack for special things
      #
      # -- PARAMETER FORMAT --
      # {KEY:VALUE, ...}
      #
      # -- XML INPUT --
      # <KEY>
      #    <foo VALUE="aaa">xxx</foo>
      #    <foo VALUE="bbb">yyy</foo>
      #    ...
      # </KEY>
      #
      # -- PYTHON OUTPUT --
      # KEY:[{"xxx":"aaa"},{"yyy":"bbb"}]
      #
      elif use_array and do_special != None and node.nodeName in do_special.keys():
         section = {}
         section[child.firstChild.data] = \
               child.attributes[do_special[node.nodeName]].value
         array.append(section)

      # I think the ugly hacks are starting to be overkill
      #
      # -- PARAMETER FORMAT --
      # {KEY:VALUE, ...}
      #
      # -- XML INPUT --
      # <KEY VALUE="aaa" ...>"xxx"</KEY>
      #
      # -- PYTHON OUTPUT --
      # KEY:["xxx","aaa"]
      #
      elif do_special2 != None and node.nodeName in do_special2.keys():
         array2 = []
         array2.append( child.firstChild.data )
         for item in do_special2[node.nodeName]:
            array2.append( child.attributes[do_special[node.nodeName]].value )
         section[node.nodeName]

      # normal way (but will overwrite lists)
      else:
         section[child.nodeName] = child.firstChild.data

      i = i+1

   # return
   if use_array:
      return array, i
   else:
      return section, i



def save(xmlfile, data, basetag, tag, has_name=True, do_array=None, do_special=None, do_special2=None):
   """
   do_array is a DICTIONARY, not a list here
   """
   xml = minidom.Document()

   base = xml.createElement(basetag)

   for key, value in data.items():

      elem = xml.createElement(tag)
      if has_name:
         elem.setAttribute("name",key)

         save_Tag( xml, elem, value, do_array, do_special, do_special2 )
      base.appendChild(elem)
   xml.appendChild(base)

   fp = open(xmlfile,"w")
   xml.writexml(fp, "", "", "", "UTF-8")
   fp.close()

   xml.unlink()



def save_Tag( xml, parent, data, do_array=None, do_special=None, do_special2=None ):
   for key, value in data.items():
      node = xml.createElement(key)

      # checks if it needs to parse an array instead of a dictionary
      #
      # -- PARAMETER FORMAT --
      # { KEY:VALUE, ... }
      #
      # -- PYTHON INPUT
      # KEY:["xxx","yyy",....]
      #
      # -- XML OUTPUT --
      # <KEY>
      #    <VALUE>xxx</VALUE>
      #    <VALUE>yyy</VALUE>
      #    ...
      # </KEY>
      #
      if do_array != None and key in do_array.keys():
         for text in value:
            node2 = xml.createElement( do_array[key] )
            txtnode = xml.createTextNode( str(text) )
            node2.appendChild(txtnode)
            node.appendChild(node2)
      
      # checks to see if we need to run the ULTRA UBER HACK
      #
      # -- PARAMETER FORMAT --
      # { KEY:[VALUE1, VALUE2] }
      #
      # -- PYTHON INPUT --
      # KEY:[{"xxx":"aaa"},{"yyy":"bbb"}]
      #
      # -- XML OUTPUT --
      # <KEY>
      #    <VALUE1 VALUE2="aaa">xxx</VALUE1>
      #    <VALUE1 VALUE2="bbb">yyy</VALUE1>
      #    ...
      # </KEY>
      #
      elif do_special != None and key in do_special.keys():
         for item in value:
            for key2, value2 in item.items(): # should only be one member
               node2 = xml.createElement( do_special[key][0] )
               node2.setAttribute(do_special[key][1], value2)
               txtnode = xml.createTextNode( str(key2) )
               node2.appendChild(txtnode)
               node.appendChild(node2)
      
      # if you thought the last hack was the ULTRA UBER HACK, think again
      #
      # -- PARAMETER FORMAT --
      # { KEY1:VALUE, ... }
      #
      # -- PYTHON INPUT --
      # KEY:{"xxx":"aaa"}
      #
      # -- XML OUTPUT --
      # <KEY VALUE="aaa">"xxx"</KEY>
      #
      elif do_special2 != None and key in do_special2.keys():
         for key2, value2 in value.items(): # should only be one member
            txtnode = xml.createTextNode( str(key2) )
            node.appendChild(txtnode)
            node.setAttribute( do_special2[key], value2 )

      elif isinstance(value,dict):
         save_Tag( xml, node, value, do_array, do_special, do_special2 )

      # standard dictionary approach
      else:
            txtnode = xml.createTextNode( str(value) )
            node.appendChild(txtnode)

      parent.appendChild(node)

