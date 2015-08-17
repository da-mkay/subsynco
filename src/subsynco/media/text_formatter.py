#!/usr/bin/env python
'''
SubSynco - a tool for synchronizing subtitle files
Copyright (C) 2015  da-mkay

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from gi.repository import GLib

import re


class TextFormatter(object):
    def __init__(self):
        self._brace_pat = re.compile('[<>]')
        self._tag_pat = re.compile('(/?u|/?i|/?b|(font( color="?([^"]*)"?)?\s*)'
                                   '|/font)$', re.IGNORECASE)
        self._empty_tag_pat = re.compile('(<u></u>|<i></i>|<b></b>|<font( [^>]*'
                                         ')?></font>|<span( [^>]*)?></span>)')

    def fix_format(self, msg, pango_markup=False):
        """Return a fixed version of msg that ensures that the format
        syntax is correct.
        
        Missing start/end-tags of format tags (b, i, u, font) will be
        added and invalid nesting of tags will be fixed.
        Other tags or special characters (<, >, &, ...) remain unchanged
        unless pango_markup is set to True. If that is the case then
        these characters will be escaped. Moreover <font>-tags will be
        converted to <span>-tags so that the string can be used where
        pango markup is required and other tags would lead to an error.
        """
        if pango_markup:
            txt_wrap = lambda x: GLib.markup_escape_text(x)
            font_tag = 'span'
            font_color_attr = 'foreground'
        else:
            txt_wrap = lambda x: x
            font_tag = 'font'
            font_color_attr = 'color'
    
        new_msg = ''
        brace_opened = False
        opened_tags = []
        pos = 0
        while True:
            brace_match = self._brace_pat.search(msg, pos)
            if not brace_match:
                if brace_opened:
                    # There was a single '<': keep it
                    new_msg += txt_wrap('<')
                new_msg += txt_wrap(msg[pos:])
                while opened_tags:
                    tag = opened_tags.pop()[0]
                    new_msg += '</'+(font_tag if tag=='font' else tag)+'>'
                break
            brace = brace_match.group()
            if brace == '<':
                if brace_opened:
                    # There was already a single '<': keep it
                    new_msg += txt_wrap('<')
                new_msg += txt_wrap(msg[pos:brace_match.start()])
                pos = brace_match.end()
                brace_opened = True
            elif brace == '>':
                tag = msg[pos:brace_match.start()]
                pos = brace_match.end()
                if brace_opened:
                    brace_opened = False
                    tag_match = self._tag_pat.match(tag)
                    if tag_match:
                        tag = tag.lower()
                        if tag[0] == '/':
                            # closing tag
                            tag = tag[1:]
                            if not opened_tags:
                                # missing opening tag
                                if tag != 'font':
                                    new_msg = '<'+tag+'>'+new_msg+'</'+tag+'>'
                                # else: tag is removed since we don't
                                #       know the color
                            elif opened_tags[-1][0] != tag:
                                open_tag_end_pos = opened_tags[-1][1]
                                # missing opening tag
                                if tag != 'font':
                                    new_msg = (new_msg[:open_tag_end_pos]+'<'+
                                               tag+'>'+
                                               new_msg[open_tag_end_pos:]+
                                               '</'+tag+'>')
                                # else: tag is removed since we don't
                                #       know the color
                            else:
                                new_msg += ('</'+(font_tag if tag=='font' else
                                                  tag)+'>')
                                opened_tags.pop() # 
                        else:
                            # opening tag
                            new_msg += ('<'+(font_tag if tag=='font' else tag)+
                                        '>' if len(tag) < 5 else '<'+font_tag+
                                        ' '+font_color_attr+'="'+
                                        tag_match.group(4).strip()+'">')
                            # (tag, endPos)
                            opened_tags.append((tag if len(tag) == 1 else
                                                'font', len(new_msg)))
                    else:
                        # unknown tag: keep braces
                        new_msg += txt_wrap('<'+tag+'>')
                else:
                    # missing '<': keep single '>'
                    new_msg += txt_wrap(tag + '>')
        
        # remove empty tags, for example '<i></i>'
        while True:
            empty_match = self._empty_tag_pat.search(new_msg)
            if not empty_match:
                break
            new_msg = (new_msg[:empty_match.start()] +
                       new_msg[empty_match.end():])

        return new_msg


if __name__ == '__main__':
    import sys
    pango_markup = False
    if len(sys.argv)>1:
        pango_markup = True
    text_formatter = TextFormatter()
    # <i>asd</i>
    print text_formatter.fix_format('<i>asd &', pango_markup)
    # <i>asd</i>
    print text_formatter.fix_format('asd</i>', pango_markup)
    # <i>a</i>
    print text_formatter.fix_format('<i>a</i>', pango_markup)
    # b<i>a</i>c
    print text_formatter.fix_format('b<i>a</i>c', pango_markup)
    # b<i>a<u>b</u>c</i>
    print text_formatter.fix_format('b<i>a<u>b</u>c</i>', pango_markup)
    # <i><i>a</i>b</i>c
    print text_formatter.fix_format('a</i>b</i>c', pango_markup)
    # a<i>b<i>c</i></i>
    print text_formatter.fix_format('a<i>b<i>c', pango_markup)
    # a<i>b<u><i>c</i>d</u>e</i>
    print text_formatter.fix_format('a<i>b<u>c</i>d</u>e', pango_markup)
    # a<b<i>c</i>
    print text_formatter.fix_format('a<b<i>c', pango_markup)
    # a>b<i>c</i>
    print text_formatter.fix_format('a>b<i>c', pango_markup)
    # a<i>b>c</i>
    print text_formatter.fix_format('a<i>b>c', pango_markup)
    # a<i>b<c</i>
    print text_formatter.fix_format('a<i>b<c', pango_markup)
    # a>b<c
    print text_formatter.fix_format('a>b<c', pango_markup)
    # some text: 4 > 3
    print text_formatter.fix_format('some text: 4 > 3', pango_markup)
    # some text: 3 < 4
    print text_formatter.fix_format('some text: 3 < 4', pango_markup)
    # some text: <i>4 > 3</i>
    print text_formatter.fix_format('some text: <i>4 > 3</i>', pango_markup)
    # some text: <i>3 < 4</i>
    print text_formatter.fix_format('some text: <i>3 < 4</i>', pango_markup)
    # some text: 4 > <i>3</i>
    print text_formatter.fix_format('some text: 4 > <i>3</i>', pango_markup)
    # some text: 3 < <i>4</i>
    print text_formatter.fix_format('some text: 3 < <i>4</i>', pango_markup)
    # 3 < 4 and 4 > 3
    print text_formatter.fix_format('3 < 4 and 4 > 3', pango_markup)
    # 3<4 and 4>3
    print text_formatter.fix_format('3<4 and 4>3', pango_markup)
    # <foo>xyz<bar>
    print text_formatter.fix_format('<foo>xyz<bar>', pango_markup)

    # <x>a<y><font>sd</x></font>
    print text_formatter.fix_format('<x>a<y><font>sd</x></font>', pango_markup)
    # <x>a<y><font color="red">sd</x></font>
    print text_formatter.fix_format('<x>a<y><font color=red>sd</x></font>',
                                    pango_markup)
    # <x>a<y><font color="green">sd</x></font>
    print text_formatter.fix_format('<x>a<y><font color="green">sd</x></font>',
                                    pango_markup)
    # <x>a<y><font color="#000">sd</x></font>
    print text_formatter.fix_format('<x>a<y><font color="#000">sd</x></font>',
                                    pango_markup)
    # <x>a<y><font color="#000">sd</x></font>
    print text_formatter.fix_format('<x>a<y><font color="#000 ">sd</x></font>',
                                    pango_markup)
    # <x>a<y><font color="#000">sd</x></font>
    print text_formatter.fix_format('<x>a<y><font color="#000" >sd</x></font>',
                                    pango_markup)
    # <x>a<y><font color="#000">sd</x></font>
    print text_formatter.fix_format('<x>a<y><font color="#000 " >sd</x></font>',
                                    pango_markup)
    # <x>a<y><font color="">sd</x></font>
    print text_formatter.fix_format('<x>a<y><font color="" >sd</x></font>',
                                    pango_markup)

    # <i>Hi there</i>
    print text_formatter.fix_format('<i>Hi there<i>', pango_markup)
    # <font color="blue"><i>Hi there</i></font>
    print text_formatter.fix_format('<font color="blue"><i>Hi there<i>',
                                    pango_markup)
    # <i>Hi there</i>
    print text_formatter.fix_format('<i>Hi there<i><font color="blue">',
                                    pango_markup)


