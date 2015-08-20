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

import codecs
import hashlib
import itertools
import json
import re
from collections import OrderedDict
from os import path
from subsynco.media.subtitle import Subtitle
from subsynco.media.subtitle import SubtitleList
from subsynco.utils.textfile import TextFile
from subsynco.utils.time import Time


class Submod(object):
    """Submod is used to load and run Submod-scripts which automatically
    modify SubtitleLists.
    
    Submod-scripts are text-files containing a single JSON-object of
    with following schema:

        {
         "subtitle": {
          "filename": "foo_bar.srt",
          "sha256":
            "b2c8ff84e3d4902fdc504e7505d60b5bfaedbae9fa1bcd71e6c0c39a92d
            00f12"
         },
         "move": [
          {"id": "1-10", "by": "+00:00:00.100"},
          {"id": "11-20", "by": "-00:00:00.110"}
         ],
         "update": [
          {"id": 21, "start": "00:00:12.000", "end": "00:00:13.000",
           "text": "Modified"}
         ],
         "remove": [
          {"id": "22-30"}
         ],
         "add": [
          {"start": "00:00:12.345", "end": "00:00:13.345",
           "text": "Timings by\nSubSynco"}
         ]
        }

    The example-script is intended to be used for subtitle-files with a
    name of "foo_bar.srt" and a sha256 checksum of "b2c8f...". The
    script will move the subtitles 1 to 20 (incl.) by 100 milliseconds 
    and the subtitles 11 to 20 by -110 milliseconds. The subtitle having
    the id 21 will be modified and the subtitles 22 to 30 will be
    removed. Moreover a new subtitle will be added at position
    "00:00:12.345".
    """
    def __init__(self, orig_subtitle_path=None, orig_subtitle_list=None,
                 orig_subtitle_encoding=None):
        """Constructor
        
        You may pass the path, SubtitleList and encoding of the original
        subtitle file. The information about the original subtitle file
        will be used when generating a Submod-script. For example the
        hash of the subtitle file will be generated and the SubtitleList
        will be compared to the new one.
        
        If you only want to run a Submod-script you don't need to pass
        a path/SubtitleList/encoding.
        """
        self.script = None
        if orig_subtitle_path is None or orig_subtitle_list is None:
            self._orig_subtitle_list = None
            self._subtitle_filename = None
            self._subtitle_sha256 = None
            self._orig_subtitle_encoding = None
        else:
            self._orig_subtitle_list = orig_subtitle_list
            __, self._subtitle_filename = path.split(orig_subtitle_path)
            self._subtitle_sha256 = self._hash_subtitle_file(orig_subtitle_path)
            self._orig_subtitle_encoding = orig_subtitle_encoding
    
    def load(self, path_, enc):
        """Loads the Submod-script file.
        
        An Exception will be raised if the script is not valid
        (ValueError, TypeError, KeyError).
        """
        with codecs.open(path_, 'r', encoding=enc) as f:
            json_data = json.load(f)
        self._validate(json_data)
        self.script = json_data
        if 'timings-for' not in self.script:
            self.script['timings-for'] = 'original'

    def _validate(self, value):
        """Validates the loaded JSON-data to ensure it is a valid
        Submod-script.
        
        If validation fails an Exception is raised (ValueError,
        TypeError, KeyError).
        """
        item_validators = {
            'subtitle': self._validate_subtitle,
            'move': self._create_list_validator(self._validate_move_item),
            'update': self._create_list_validator(self._validate_update_item),
            'remove': self._create_list_validator(self._validate_remove_item),
            'add': self._create_list_validator(self._validate_add_item)
        }
        opt_item_validators = {
            'timings-for': self._validate_timings_for
        }
        self._validate_dict(value, item_validators,
                            opt_item_validators=opt_item_validators)

    def _validate_subtitle(self, value):
        item_validators = {
            'filename': self._validate_any_str,
            'sha256': lambda v: self._validate_str(v, r'^[0-9a-f]{64}$')
        }
        optional_items_validators = {
            'encoding': self._validate_encoding
        }
        self._validate_dict(value, item_validators,
                            opt_item_validators=optional_items_validators)

    def _validate_move_item(self, value):
        item_validators = {
            'id': self._validate_id,
            'by': self._validate_signed_time,
        }
        self._validate_dict(value, item_validators)
            
    def _validate_update_item(self, value):
        # id is required
        item_validators = {
            'id': self._validate_id
        }
        # but we need only one of start, end or text
        any_item_validators = {
            'start': self._validate_time,
            'end': self._validate_time,
            'text': self._validate_any_str,
        }
        self._validate_dict(value, item_validators, any_item_validators)

    def _validate_remove_item(self, value):
        item_validators = {
            'id': self._validate_id
        }
        self._validate_dict(value, item_validators)

    def _validate_add_item(self, value):
        item_validators = {
            'start': self._validate_time,
            'end': self._validate_time,
            'text': self._validate_any_str,
        }
        self._validate_dict(value, item_validators)

    def _validate_timings_for(self, value):
        self._validate_str(value, r'^(original|uncut)$')

    def _validate_time(self, value):
        self._validate_str(value, r'^\d{2}:[0-5]\d:[0-5]\d\.\d{3}$')

    def _validate_signed_time(self, value):
        self._validate_str(value, r'^[+-]\d{2}:[0-5]\d:[0-5]\d\.\d{3}$')

    def _validate_id(self, value):
        if isinstance(value, int) or isinstance(value, long):
            return
        groups = self._validate_str(value, r'^(\d+)-(\d+)$')
        if long(groups[0]) >= long(groups[1]):
            raise ValueError(_('Invalid ids in Submod-script!'))

    def _validate_encoding(self, value):
        self._validate_any_str(value)
        if value not in TextFile.get_available_encodings():
            raise TypeError(_('Invalid encoding ({}) in Submod-script!').format(
                                                                         value))
        
    def _validate_any_str(self, value):
        if not isinstance(value, unicode):
            raise TypeError(_('Invalid Submod-script! Expected string, but foun'
                              'd:\n{}').format(json.dumps(value)))
        
    def _validate_str(self, value, regex):
        self._validate_any_str(value)
        match = re.match(regex, value)
        if match is None:
            raise ValueError(_('Invalid "{}" in Submod-script!').format(value))
        return match.groups()

    def _create_list_validator(self, item_validator):
        return lambda v: self._validate_list(v, item_validator)

    def _validate_list(self, value, item_validator):
        """Validates that the given value is a list and validates each
        list item using the given item_validator.
        """
        if not isinstance(value, list):
            raise TypeError(_('Invalid Submod-script! Expected array, but found'
                              ':\n{}').format(json.dumps(value)))
        for item in value:
            item_validator(item)

    def _validate_dict(self, value, item_validators, any_item_validators={},
                       opt_item_validators={}):
        """Validates that the given value is a dict and that the dict
        itself is valid.
        
        The dict is considered to be valid if the following is true:
          1. item_validators, any_item_validators and
             opt_item_validators contain the valid keys. Each key of
             the dict value must be a valid key.
          2. The dict value must contain all keys of item_validators.
          3. The dict value must contain at least one key of
             any_item_validators.
          4. item_validators, any_item_validators and
             opt_item_validators also contain a validation method for
             each valid key. These are used to validate the dict'
             values.

        Each *_valiators-parameter is a dict that assigns a validator-
        function to a key, for example: {'id': self._validate_id}. In
        this case the dict's 'id' value is validated using the method
        self._validate_id.
        """
        if not isinstance(value, dict):
            raise TypeError(_('Invalid Submod-script! Expected object, but foun'
                              'd:\n{}').format(json.dumps(value)))
        for key, v in value.iteritems():
            if key in item_validators:
                item_validators[key](v)
            elif key in any_item_validators:
                any_item_validators[key](v)
            elif key in opt_item_validators:
                opt_item_validators[key](v)
            else:
                raise ValueError(
                                _('Unknown "{}" in Submod-script!').format(key))
        for key in item_validators:
            if key not in value:
                raise KeyError(_('Missing "{}" in Submod-script!').format(key))
        if len(any_item_validators) > 0 and len(value) <= len(item_validators):
            raise KeyError(_('Missing one of "{}" in Submod-script!').format(
                                       '", "'.join(any_item_validators.keys())))

    def _get_ids_for_script(self, id1, id2):
        return id1 if id1 == id2 else "{}-{}".format(str(id1), str(id2))

    def _get_valid_ids(self, subtitle_list, value):
        """Get a list of valid subtitle ids.
        
        For example 1 will return [0] and "3-6" will return
        [2, 3, 4, 5].
        
        If any of the ids is not contained in the SubtitleList an
        IndexError is raised.
        """
        if isinstance(value, int) or isinstance(value, long):
            range_ = [value, value]
        else:
            range_ = map(long, value.split('-'))
        range_[0] -= 1
        ids = range(*range_)
        max_valid_id = len(subtitle_list) - 1
        not_found = filter(lambda id_: id_>max_valid_id, ids)
        if not_found:
            raise IndexError(_('Subtitle(s) "{}" not found!').format(
                               '", "'.join(map(lambda v: str(v+1), not_found))))
        return ids

    def _get_subtitles_by_ids(self, subtitle_list, ids):
        id_list = self._get_valid_ids(subtitle_list, ids)
        return map(lambda id_: subtitle_list[id_], id_list)

    def _hash_subtitle_file(self, path_):
        sha256 = hashlib.sha256()
        with open(path_, 'rb') as f:
            buf = f.read()
            sha256.update(buf)
        return sha256.hexdigest()

    def run(self, path_, subtitle_loader, cuts=None):
        """Loads a SubtitleList from the subtitle file path_ using the
        given subtitle_loader function and applies the loaded Submod-
        script.
        
        subtitle_loader must be a function that accept a path as
        parameter and returns a SubtitleList.
        
        If cuts is set then the timings are adapted for these cuts so
        that the created subtitle and the cut video are in sync.
        
        The changes are always made in the following order: move,
        update, remove, add.

        NOTE: All ids specified in the Submod-script refer to the
              subtitles in the original/unchanged SubtitleList. If for
              example you specify multiple items in the "remove"-
              section you don't need to take into account that removing
              a subtitle will change the id of following subtitles.
        
        A ValueError/IndexError may be raised, for example if the
        subtitle file has a wrong checksum or if a subtitle was not
        found.
        
        Returns a SubtitleList.
        """
        # NOTE: We do not use SubtitleList's methods to modify the
        #       timestamps of subtitles. For example move_subtitle()
        #       could change the order of the subtitles so that the id's
        #       from the submod may not refer to the correct subtitle
        #       anymore. Instead we modify the subtitle's start/end
        #       values directly which will result in a SubtitleList that
        #       is not properly ordered. After moving, updating and
        #       removing subtitles we add all subtitles of the current
        #       SubtitleList to a new SubtitleList which then will take
        #       care of the correct order of the subtitles based on
        #       their timestamps. At the end we add the new subtitles
        #       from the add-section of the submod.
        sha256 = self._hash_subtitle_file(path_).lower()
        if sha256 != self.script['subtitle']['sha256']:
            raise ValueError(_('The subtitle has a wrong checksum ("{}")!')
                             .format(sha256))
        subtitle_list = subtitle_loader(path_)
        offset = 0.0
        for move in self.script['move']:
            by = Time.millis_from_str(move['by'])
            for i in self._get_valid_ids(subtitle_list, move['id']):
                if cuts is not None:
                    offset = self._get_run_offset(subtitle_list[i].start + by,
                                                  cuts)
                subtitle_list[i].start = (subtitle_list[i].start + by) - offset
                subtitle_list[i].end = (subtitle_list[i].end + by) - offset
        for update in self.script['update']:
            # Each update may contain any of end, start and text values
            # where the end/start-strings must be converted to number of
            # milliseconds.
            new_values = []
            for k, f in [('start', lambda x : self._get_run_time(
                                                Time.millis_from_str(x), cuts)),
                         ('end', lambda x : self._get_run_time(
                                                Time.millis_from_str(x), cuts)),
                         ('text', lambda x : x.encode('utf-8'))]:
                if k in update:
                    new_values.append((k, f(update[k],)))
            subtitles = self._get_subtitles_by_ids(subtitle_list, update['id'])
            for subtitle in subtitles:
                for k, v in new_values:
                    setattr(subtitle, k, v)
        # Gather ids of subs that should be removed and sort them desc.
        # The subs are removed in that order. Thus the sub with the 
        # biggest id will be removed first. If we would start with a
        # smaller id, then further ids that should be removed will point
        # to a wrong subtitle.
        to_remove = []
        for remove in self.script['remove']:
            to_remove += self._get_valid_ids(subtitle_list, remove['id'])
        for i in sorted(to_remove, reverse=True):
            subtitle_list.remove_subtitle(i)
        new_subtitle_list = SubtitleList()
        for subtitle in subtitle_list:
            new_subtitle_list.add_subtitle(subtitle)
        for add in self.script['add']:
            start = self._get_run_time(Time.millis_from_str(add['start']), cuts)
            end = self._get_run_time(Time.millis_from_str(add['end']), cuts)
            subtitle = Subtitle(start, end, add['text'].encode('utf-8'))
            new_subtitle_list.add_subtitle(subtitle)
        return new_subtitle_list

    def generate_script(self, subtitle_list, cuts=None):
        """Generate a Submod-script by comparing the original and new
        SubtitleList.
        
        You should use this method only if the Submod-object was created
        using the path and SubtitleList of the original subtitle file.
        Otherwise a ValueError is raised.
        
        If cuts is set the Submod-script will export timings that will
        fit to the uncut video instead of the cut video. Thus the
        Submod-script can be used for a different cutlist as well.
        """
        if self._orig_subtitle_list is None:
            raise ValueError(_('Failed to generate Subdmod-script: the original'
                               ' subtitle list is missing)!'))
        # We use OrderedDicts so that the exported JSON will be more
        # readable.
        script = OrderedDict([
            ('subtitle', OrderedDict([
                ('filename', self._subtitle_filename.decode('utf-8')),
                ('sha256', self._subtitle_sha256)])
            ),
            ('timings-for', 'original'),
            ('move', []),
            ('update', []),
            ('remove', []),
            ('add', []),
        ])
        if self._orig_subtitle_encoding is not None:
            script['subtitle']['encoding'] = self._orig_subtitle_encoding
        if cuts is not None:
            script['timings-for'] = 'uncut'
        # Check which subtitles were moved (start/end-time changed by
        # the same amount, anything else unchanged) and which subtitles
        # were updated or added.
        # New subtiles will be added directly to the script. Moved and
        # updated subtitles will be added to tmp-dicts which will be
        # used to merge subtitles with the same changes and successive
        # ids. For example if subtitle 1 and subtitle 2 were both moved
        # by 100 ms then only one move-item will be generated for the
        # id "1-2".
        tmp_updates_by_id = {} # {id: {start:X, end:Y, text:Z}, ...}
        tmp_moves_by_id = {} # {id: time_diff, ...}
        processed_ids = [] # moves/updates were generated for these ids
        offset = 0.0
        for subtitle in subtitle_list:
            if subtitle.orig_id is None:
                # subtitle was not in file before
                script['add'].append(OrderedDict([
                    ('start', self._get_export_time(subtitle.start, cuts)),
                    ('end', self._get_export_time(subtitle.end, cuts)),
                    ('text', subtitle.text.decode('utf-8'))
                ]))
            else:
                # subtitle was in file before --> update or move
                processed_ids.append(subtitle.orig_id)
                start_diff = subtitle.start - subtitle.orig_start
                end_diff = subtitle.end - subtitle.orig_end
                text_changed = (subtitle.text != subtitle.orig_text)
                # TODO handle optional coordinates (X1, X2, Y1, Y2)
                if (text_changed or start_diff != end_diff):
                    # text has changed or start/end time were changed
                    # differently (--> update instead of move)
                    tmp_update = []
                    if start_diff != 0:
                        tmp_update.append(('start',
                                  self._get_export_time(subtitle.start, cuts),))
                    if end_diff != 0:
                        tmp_update.append(('end',
                                    self._get_export_time(subtitle.end, cuts),))
                    if text_changed:
                        tmp_update.append(
                                       ('text', subtitle.text.decode('utf-8'),))
                    tmp_updates_by_id[subtitle.orig_id] = tmp_update
                elif start_diff != 0:
                    if cuts is not None:
                        offset = self._get_export_offset(subtitle.start, cuts)
                            
                    tmp_moves_by_id[subtitle.orig_id] = (start_diff, offset)
                # else: subtitle has not changed
        # Updates
        todo_update_list = self._merge_by_ids(tmp_updates_by_id)
        for id1, id2, tmp_update in todo_update_list:
            new_update = [('id', self._get_ids_for_script(id1, id2))]
            new_update.extend(tmp_update)
            script['update'].append(OrderedDict(new_update))
        # Moves
        todo_move_list = self._merge_by_ids(tmp_moves_by_id)
        for id1, id2, (time_diff, offset) in todo_move_list:
            # NOTE: We do not pass  cuts here since the offset was 
            #       already calculated based on the cuts (s.a.)
            move_by = self._get_export_time(offset + time_diff)
            sign = '+' if move_by[0]!='-' else ''
            script['move'].append(OrderedDict([
                ('id', self._get_ids_for_script(id1, id2)),
                ('by', sign + move_by)
            ]))
        # Check which subtitles of the original SubtitleList were
        # removed. Then add remove-items to the script (merging
        # successive ids).
        tmp_removes_by_id = {} # {id: None, ...}
        for subtitle in self._orig_subtitle_list:
            if (subtitle.orig_id is not None
                    and subtitle.orig_id not in processed_ids):
                tmp_removes_by_id[subtitle.orig_id] = None
        todo_remove_list = self._merge_by_ids(tmp_removes_by_id)
        for id1, id2, __ in todo_remove_list:
            script['remove'].append(OrderedDict([
                ('id', self._get_ids_for_script(id1, id2))
            ]))
        self.script = script

    def convert_origial_to_uncut(self, path_, subtitle_loader, cuts):
        """Converts a submod-script with "timings-for" set to "original"
        to a submod-script with "timings-for" set to "uncut". So the
        submod-script can be used with other cutlists, too.
        """
        sha256 = self._hash_subtitle_file(path_).lower()
        if sha256 != self.script['subtitle']['sha256']:
            raise ValueError(_('The subtitle has a wrong checksum ("{}")!')
                             .format(sha256))
        subtitle_list = subtitle_loader(path_)
        tmp_moves_by_id = {}
        for move in self.script['move']:
            by = Time.millis_from_str(move['by'])
            for i in self._get_valid_ids(subtitle_list, move['id']):
                offset = self._get_export_offset(
                                              subtitle_list[i].start + by, cuts)
                tmp_moves_by_id[subtitle_list[i].orig_id] = (by, offset)
        self.script['move'] = []
        # Moves
        todo_move_list = self._merge_by_ids(tmp_moves_by_id)
        for id1, id2, (time_diff, offset) in todo_move_list:
            # NOTE: We do not pass  cuts here since the offset was 
            #       already calculated based on the cuts (s.a.)
            move_by = self._get_export_time(offset + time_diff)
            sign = '+' if move_by[0]!='-' else ''
            self.script['move'].append(OrderedDict([
                ('id', self._get_ids_for_script(id1, id2)),
                ('by', sign + move_by)
            ]))
        for update in self.script['update']:
            if 'start' in update:
                update['start'] = self._get_export_time(
                                    Time.millis_from_str(update['start']), cuts)
            if 'end' in update:
                update['end'] = self._get_export_time(
                                      Time.millis_from_str(update['end']), cuts)
        for add in self.script['add']:
            add['start'] = self._get_export_time(
                                       Time.millis_from_str(add['start']), cuts)
            add['end'] = self._get_export_time(
                                         Time.millis_from_str(add['end']), cuts)
        self.script['timings-for'] = 'uncut'

    def _get_export_offset(self, millis, cuts):
        offset = 0.0
        for start, duration, cut in cuts:
            offset = start - (cut - duration)
            if millis < long(cut):
                return offset
        return offset

    def _get_export_time(self, millis, cuts=None):
        if cuts is None:
            return Time.format(millis)
        offset = self._get_export_offset(millis, cuts)
        return Time.format(offset + millis)

    def _get_run_offset(self, millis, cuts):
        offset = 0.0
        for start, duration, cut in cuts:
            offset = start - (cut - duration)
            if millis < start+duration:
                return offset
        return offset

    def _get_run_time(self, millis, cuts=None):
        if cuts is None:
            return millis
        offset = self._get_run_offset(millis, cuts)
        return millis - offset

    def _merge_by_ids(self, vals_by_id):
        """Merges successive ids with the same value.
        
        Returns a list of [id1, id2, value]-objects such that
        vals_by_id maps each key from id1 to id2 (incl.) to value.
        
        Example:
        If vals_by_id is {1:'a', 3:'b', 2:'a'} then the following would
        be returned: [[1, 2, 'a'], [3, 3, 'b']]
        """
        merged_ids = []
        for id_ in sorted(vals_by_id.keys()):
            new = True
            new_value = vals_by_id[id_]
            if merged_ids:
                id1, id2, value = merged_ids[-1]
                if id2+1==id_ and value==new_value:
                    merged_ids[-1][1] = id_
                    new = False
            if new:
                merged_ids.append([id_, id_, new_value])
        return merged_ids

    def save_script(self, path_):
        with codecs.open(path_, 'w', encoding='utf8') as f:
            json.dump(self.script, f, indent=2, sort_keys=False,
                      ensure_ascii=False)

